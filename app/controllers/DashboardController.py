from flask import Blueprint, render_template, url_for, flash, redirect
from flask_login import login_required, current_user
from app.market_service import fetch_live_market_data
# Importaciones de Modelos (Asegúrate de importar Transaction)
from app.models import Holding, Transaction # <<< CAMBIO CLAVE: Agregada Transaction
from datetime import datetime, timedelta
# Para consultas rápidas de Transacciones
from sqlalchemy import desc # <<< CAMBIO CLAVE: Agregada importación
# yfinance y pandas se usan en el bloque de histórico, lo mantenemos.
import pandas as pd
import yfinance as yf 

# --- Definir Blueprint ---
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def dashboard():
    # 1. Obtener datos de la base de datos (RÁPIDO)
    holdings = Holding.query.filter_by(user_id=current_user.id).all()
    
    # Obtener las últimas 20 transacciones para el historial
    transaction_history = Transaction.query.filter_by(user_id=current_user.id)\
                                     .order_by(desc(Transaction.timestamp))\
                                     .limit(20).all() # <<< CAMBIO CLAVE: Consulta de Historial

    # 2. Obtener datos del mercado en vivo (USA CACHÉ de 10 minutos)
    try:
        # Esta llamada solo es lenta si la caché de 10 minutos está expirada.
        _, products_dict = fetch_live_market_data() 
    except Exception as e:
        print(f"ERROR: Fallo al obtener datos del mercado (Caché): {e}")
        products_dict = {}

    valor_portafolio = 0
    portafolio_data = []

    # --- 3. Calcular valores actuales y portafolio_data ---
    for h in holdings:
        symbol = h.symbol
        market_info = products_dict.get(symbol, {})
        
        # Usamos el precio del mercado cacheado, con el precio de compra como fallback
        current_price = market_info.get('price', h.purchase_price)

        try:
            current_price = float(current_price)
        except (TypeError, ValueError):
            current_price = h.purchase_price

        # Cálculos de P&L
        current_value = current_price * h.quantity
        gain_loss = current_value - (h.purchase_price * h.quantity)
        percent_change = (gain_loss / (h.purchase_price * h.quantity)) * 100 if h.purchase_price * h.quantity > 0 else 0

        valor_portafolio += current_value

        portafolio_data.append({
            'id': h.id,
            'symbol': h.symbol,
            'name': market_info.get('name', h.name),
            'quantity': h.quantity,
            'purchase_price': h.purchase_price,
            'current_price': current_price,
            'gain_loss': gain_loss,
            'percent_change': percent_change,
            'total_value': current_value
        })

    current_capital = float(current_user.capital)
    total_capital = current_capital + valor_portafolio
    
    # Lógica de P&L global (Asumimos 10000.00 de capital inicial)
    initial_capital_value = 10000.00
    overall_pnl = total_capital - initial_capital_value
    overall_pnl_pct = (overall_pnl / initial_capital_value * 100) if initial_capital_value > 0 else 0.0


    # --- 4. Obtener datos históricos para el gráfico (Manteniendo la lógica optimizada) ---
    # Nota: Si el rendimiento sigue siendo un problema, este es el bloque a mover 
    # a una llamada asíncrona (AJAX) o a una tarea en segundo plano.
    num_days = 7
    portfolio_history = {"labels": [], "values": []}
    
    # Generar etiquetas de fechas
    date_labels = []
    for i in range(num_days):
        day = datetime.now() - timedelta(days=num_days - 1 - i)
        date_labels.append(day.strftime("%Y-%m-%d"))
    portfolio_history["labels"] = date_labels

    if portafolio_data:
        # Obtener todos los símbolos del portafolio
        symbols_in_portfolio = [item['symbol'] for item in portafolio_data]
        quantity_map = {item['symbol']: item['quantity'] for item in portafolio_data}

        try:
            start_date = (datetime.now() - timedelta(days=num_days)).strftime('%Y-%m-%d')
            
            # ¡Una sola llamada a la API para todos los símbolos!
            # Mantenemos esta lógica optimizada para la consulta de varios símbolos
            hist_data = yf.download(
                symbols_in_portfolio, 
                start=start_date, 
                interval="1d"
            )

            daily_portfolio_values = [0.0] * num_days
            
            if not hist_data.empty:
                prices_df = hist_data['Close'].tail(num_days)

                for symbol in symbols_in_portfolio:
                    quantity = quantity_map[symbol]
                    
                    # Adaptación por si yf.download devuelve solo una columna (un solo activo)
                    if len(symbols_in_portfolio) == 1 and symbol in prices_df.name:
                        price_series = prices_df
                    elif len(symbols_in_portfolio) > 1 and symbol in prices_df.columns:
                        price_series = prices_df[symbol]
                    else:
                        continue # Saltar si no se encuentra el símbolo
                        
                    asset_daily_values = (price_series * quantity).tolist()
                                        
                    # Rellenar días faltantes (si yf no devuelve 7 días)
                    if len(asset_daily_values) < num_days:
                        # Rellenar con el primer valor conocido para los días faltantes
                        missing_days = num_days - len(asset_daily_values)
                        asset_daily_values = ([asset_daily_values[0]] * missing_days) + asset_daily_values

                    # Sumar los valores de este activo al total diario
                    for i in range(num_days):
                        daily_portfolio_values[i] += asset_daily_values[i]

                # --- Combinar con capital ---
                portfolio_history["values"] = [
                    round(current_capital + daily_value, 2) for daily_value in daily_portfolio_values
                ]

        except Exception as e:
            print(f"ERROR: Fallo al obtener datos históricos para el gráfico: {e}")
            # Fallback: si la API falla, mostrar solo el capital
            portfolio_history["values"] = [round(current_capital, 2)] * num_days
            
    else:
        # Si no hay holdings, el gráfico solo muestra el capital
        portfolio_history["values"] = [round(current_capital, 2)] * num_days


    # --- Renderizar Plantilla ---
    return render_template(
        'Dashboard/dashboard.html',
        current_capital=current_capital,
        valor_portafolio=valor_portafolio,
        total_capital=total_capital,
        portafolio=portafolio_data,
        portfolio_history=portfolio_history,
        transaction_history=transaction_history, # <<< NUEVO: Historial de Transacciones
        overall_pnl=overall_pnl,
        overall_pnl_pct=overall_pnl_pct
    )


@dashboard_bp.route('/history', methods=['GET']) # <<< NUEVA RUTA
@login_required
def history():
    """
    Muestra el historial completo de transacciones del usuario.
    """
    # Consulta todas las transacciones ordenadas por fecha descendente
    # No hay límite de 20 aquí, mostramos todo el historial.
    all_transactions = Transaction.query.filter_by(user_id=current_user.id)\
                                     .order_by(desc(Transaction.timestamp))\
                                     .all()

    return render_template(
        'Dashboard/history.html', # <<< NUEVA PLANTILLA
        transactions=all_transactions
    )