from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models import Holding, Transaction
from sqlalchemy import desc
from datetime import datetime, timedelta
import yfinance as yf

# Importamos tus servicios (asegúrate de que la ruta sea correcta)
# **IMPORTANTE: Debemos cambiar el nombre de esta función**
from app.market_service import get_simple_chart_data, get_portfolio_historical_value # Nueva función

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# ==========================================
# RUTA 1: VISTA RÁPIDA (Solo Base de Datos)
# ==========================================
@dashboard_bp.route('/')
@login_required
def dashboard():
    
    holdings = Holding.query.filter_by(user_id=current_user.id).all()
    
    transaction_history = Transaction.query.filter_by(user_id=current_user.id)\
                                       .order_by(desc(Transaction.timestamp))\
                                       .limit(5).all() # Limitado a 5 para resumen

    
    return render_template(
        'Dashboard/dashboard.html',
        holdings=holdings,
        transaction_history=transaction_history,
        current_capital=current_user.capital
    )

# ==========================================
# RUTA 2: API DE DATOS (Lógica Pesada)
# ==========================================
@dashboard_bp.route('/api/data')
@login_required
def dashboard_data():
    """
    Esta función hace el trabajo pesado en segundo plano:
    1. Descarga precios en vivo SOLO de las acciones.
    2. Calcula P&L y Totales.
    3. Genera datos para el gráfico, usando el parámetro 'timeframe'.
    """
    # 1. Obtener el parámetro de tiempo (por defecto 'Todo')
    timeframe = request.args.get('timeframe', 'Todo').upper() 
    
    try:
        holdings = Holding.query.filter_by(user_id=current_user.id).all()
        
        # Si no hay inversiones, retornamos datos vacíos rápido
        if not holdings:
            # Usar la función de simulación simple para llenar el gráfico vacío
            chart_data = get_simple_chart_data(float(current_user.capital), timeframe=timeframe)
            
            return jsonify({
                'summary': {
                    'portfolio_value': 0,
                    'total_capital': float(current_user.capital),
                    'pnl': 0,
                    'pnl_pct': 0
                },
                'holdings_updates': {},
                'chart_data': chart_data
            })

        # ... (Toda la lógica de obtención de precios en vivo y cálculo de P&L se mantiene igual) ...

        # 1. Optimización: Descargar solo los tickers que tiene el usuario
        symbols = [h.symbol for h in holdings]
        # Usamos un diccionario para acceso rápido
        live_prices = {}
        
        try:
            # Descarga batch de yfinance solo para nuestros símbolos (Usamos un periodo corto, ya que solo necesitamos el precio actual)
            data = yf.download(symbols, period="5d", auto_adjust=True, progress=False)
            
            for symbol in symbols:
                # Manejo robusto de pandas/yfinance
                if len(symbols) == 1:
                    price = data['Close'].iloc[-1] if not data.empty and 'Close' in data else 0
                else:
                    # Usar .get() para manejar la posible ausencia de la columna 'Close' para un símbolo
                    close_series = data['Close'].get(symbol) 
                    price = close_series.iloc[-1] if close_series is not None and not close_series.empty else 0
                
                live_prices[symbol] = float(price)
                
        except Exception as e:
            print(f"Error API YFinance: {e}")
            # Fallback: precios a 0 si falla la API
            for s in symbols: live_prices[s] = 0

        # 2. Calcular Valores
        valor_portafolio = 0
        total_invested = 0
        holdings_updates = {} # Diccionario para actualizar la tabla por ID de holding

        for h in holdings:
            # Fallback para el precio si la API falla
            current_price = live_prices.get(h.symbol, h.purchase_price)
            if current_price <= 0: current_price = h.purchase_price # Fallback

            current_val = current_price * h.quantity
            invested_val = h.purchase_price * h.quantity
            
            valor_portafolio += current_val
            total_invested += invested_val
            
            gain = current_val - invested_val
            pct = (gain / invested_val * 100) if invested_val > 0 else 0

            # Datos para actualizar la fila específica de este holding en el frontend
            holdings_updates[h.id] = {
                'current_price': current_price,
                'total_value': current_val,
                'gain': gain,
                'pct': pct
            }

        # 3. Totales Generales
        current_capital = float(current_user.capital)
        total_capital = current_capital + valor_portafolio
        initial_capital = 10000.00 # Configurable
        overall_pnl = total_capital - initial_capital
        overall_pnl_pct = (overall_pnl / initial_capital * 100) if initial_capital > 0 else 0

        # 4. Gráfico: ¡USAMOS EL NUEVO TIMEFRAME!
        # Aquí llamarías a una función real que calcula el valor histórico del portafolio
        # Por ahora, usamos una función simulada que respeta el rango de tiempo
        
        # Si tienes holdings reales, llama a la función compleja (que simulo aquí con el mismo nombre, pero que tú deberías implementar)
        # chart_data = get_portfolio_historical_value(holdings, current_capital, timeframe) 
        
        # Por simplicidad y para que funcione con tu simulación:
        chart_data = get_simple_chart_data(total_capital, timeframe=timeframe) 


        return jsonify({
            'summary': {
                'portfolio_value': valor_portafolio,
                'total_capital': total_capital,
                'pnl': overall_pnl, # Opcional si quieres mostrar P&L global
                'pnl_pct': overall_pnl_pct
            },
            'holdings_updates': holdings_updates,
            'chart_data': chart_data
        })

    except Exception as e:
        print(f"Error en API Dashboard: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/history')
@login_required
def history():
    # Tu ruta de historial existente
    all_transactions = Transaction.query.filter_by(user_id=current_user.id)\
                                       .order_by(desc(Transaction.timestamp))\
                                       .all()
    return render_template('Dashboard/history.html', transactions=all_transactions)