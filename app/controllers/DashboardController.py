from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models import Holding, Transaction
from sqlalchemy import desc
from datetime import datetime, timedelta
import yfinance as yf

# Blueprint del dashboard: aquí centralizo todo lo que muestra datos del portafolio.
from app.market_service import get_simple_chart_data, get_portfolio_historical_value

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# ================================
# DASHBOARD PRINCIPAL (solo BD)
# ================================
@dashboard_bp.route('/')
@login_required
def dashboard():
    # Obtengo las posiciones del usuario para mostrar su estado actual.
    holdings = Holding.query.filter_by(user_id=current_user.id).all()
    
    # Últimos movimientos para el resumen rápido.
    transaction_history = Transaction.query.filter_by(user_id=current_user.id)\
                                           .order_by(desc(Transaction.timestamp))\
                                           .limit(5).all()

    return render_template(
        'Dashboard/dashboard.html',
        holdings=holdings,
        transaction_history=transaction_history,
        current_capital=current_user.capital
    )

# ==================================
# ENDPOINT PARA DATOS EN VIVO
# ==================================
@dashboard_bp.route('/api/data')
@login_required
def dashboard_data():
    # Obtengo el timeframe del gráfico que pide el usuario.
    timeframe = request.args.get('timeframe', 'Todo').upper()
    
    try:
        holdings = Holding.query.filter_by(user_id=current_user.id).all()
        
        # Si no tiene inversiones, devuelvo un gráfico vacío pero coherente.
        if not holdings:
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

        # Solo descargo precios de los símbolos que realmente tiene el usuario.
        symbols = [h.symbol for h in holdings]
        live_prices = {}

        # Intento obtener precios actuales para todos los símbolos a la vez.
        try:
            data = yf.download(symbols, period="5d", auto_adjust=True, progress=False)

            for symbol in symbols:
                # Manejo casos donde yfinance falla o viene vacío.
                if len(symbols) == 1:
                    price = data['Close'].iloc[-1] if not data.empty and 'Close' in data else 0
                else:
                    close_series = data['Close'].get(symbol)
                    price = close_series.iloc[-1] if close_series is not None and not close_series.empty else 0
                
                live_prices[symbol] = float(price)

        except Exception as e:
            print(f"Error API YFinance: {e}")
            # Si falla todo, dejo los precios en cero para no romper nada.
            for s in symbols:
                live_prices[s] = 0

        # ==========================
        # Cálculo de valores
        # ==========================
        valor_portafolio = 0
        total_invested = 0
        holdings_updates = {}

        for h in holdings:
            # Si yfinance falla, uso el precio de compra como plan B.
            current_price = live_prices.get(h.symbol, h.purchase_price)
            if current_price <= 0:
                current_price = h.purchase_price

            current_val = current_price * h.quantity
            invested_val = h.purchase_price * h.quantity
            
            valor_portafolio += current_val
            total_invested += invested_val

            gain = current_val - invested_val
            pct = (gain / invested_val * 100) if invested_val > 0 else 0

            # Datos que actualizarán la tabla del frontend en tiempo real.
            holdings_updates[h.id] = {
                'current_price': current_price,
                'total_value': current_val,
                'gain': gain,
                'pct': pct
            }

        # ==========================
        # Totales globales
        # ==========================
        current_capital = float(current_user.capital)
        total_capital = current_capital + valor_portafolio

        # Capital inicial fijo (podrías hacerlo configurable luego).
        initial_capital = 10000.00
        overall_pnl = total_capital - initial_capital
        overall_pnl_pct = (overall_pnl / initial_capital * 100) if initial_capital > 0 else 0

        # ==========================
        # Gráfico (usa timeframe)
        # ==========================
        # Si tienes implementado el histórico real del portafolio, aquí se usaría.
        # chart_data = get_portfolio_historical_value(holdings, current_capital, timeframe)

        # Por ahora usamos la función simple para que siempre funcione.
        chart_data = get_simple_chart_data(total_capital, timeframe=timeframe)

        return jsonify({
            'summary': {
                'portfolio_value': valor_portafolio,
                'total_capital': total_capital,
                'pnl': overall_pnl,
                'pnl_pct': overall_pnl_pct
            },
            'holdings_updates': holdings_updates,
            'chart_data': chart_data
        })

    except Exception as e:
        print(f"Error en API Dashboard: {e}")
        return jsonify({'error': str(e)}), 500


# ==========================
# HISTORIAL COMPLETO
# ==========================
@dashboard_bp.route('/history')
@login_required
def history():
    # Vista con todos los movimientos del usuario.
    all_transactions = Transaction.query.filter_by(user_id=current_user.id)\
                                        .order_by(desc(Transaction.timestamp))\
                                        .all()
    return render_template('Dashboard/history.html', transactions=all_transactions)
