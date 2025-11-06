from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.market_service import fetch_live_market_data
from app.models import Holding
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

# --- Definir Blueprint ---
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def dashboard():
    # Obtener todas las inversiones activas del usuario
    holdings = Holding.query.filter_by(user_id=current_user.id).all()

    # Obtener datos del mercado en vivo
    try:
        _, products_dict = fetch_live_market_data() 
    except Exception as e:
        print(f"ERROR: Fallo al obtener datos del mercado: {e}")
        products_dict = {}

    valor_portafolio = 0
    portafolio_data = []

    # --- Paso 1: calcular valores actuales y portafolio_data ---
    for h in holdings:
        symbol = h.symbol
        market_info = products_dict.get(symbol, {})
        current_price = market_info.get('price', h.purchase_price)  # Usar purchase_price como fallback

        try:
            current_price = float(current_price)
        except (TypeError, ValueError):
            current_price = h.purchase_price

        gain_loss = (current_price - h.purchase_price) * h.quantity
        percent_change = ((current_price - h.purchase_price) / h.purchase_price) * 100 if h.purchase_price > 0 else 0

        valor_portafolio += current_price * h.quantity

        portafolio_data.append({
            'id': h.id,
            'symbol': h.symbol,
            'name': market_info.get('name', h.name),
            'quantity': h.quantity,
            'purchase_price': h.purchase_price,
            'current_price': current_price,
            'gain_loss': gain_loss,
            'percent_change': percent_change,
            'total_value': current_price * h.quantity
        })

    current_capital = float(current_user.capital)
    total_capital = current_capital + valor_portafolio

    # --- Paso 2 (Refactorizado): Obtener todos los datos históricos de una vez ---
    num_days = 7
    portfolio_history = {"labels": [], "values": []}
    
    # Generar etiquetas de fechas
    date_labels = []
    for i in range(num_days):
        day = datetime.now() - timedelta(days=num_days - 1 - i)
        date_labels.append(day.strftime("%Y-%m-%d"))
    portfolio_history["labels"] = date_labels

    if not portafolio_data:
        # Si no hay portafolio, el gráfico solo muestra el capital
        portfolio_history["values"] = [round(current_capital, 2)] * num_days
    else:
        # Obtener todos los símbolos del portafolio
        symbols_in_portfolio = [item['symbol'] for item in portafolio_data]
        
        # Mapear símbolo a cantidad (para el cálculo posterior)
        quantity_map = {item['symbol']: item['quantity'] for item in portafolio_data}

        try:
            # ¡Una sola llamada a la API para todos los símbolos!
            start_date = (datetime.now() - timedelta(days=num_days)).strftime('%Y-%m-%d')
            
            # Usamos yf.download() que es mejor para esto
            # Nota: Necesitarás importar yfinance as yf en el controlador
            import yfinance as yf 
            hist_data = yf.download(
                symbols_in_portfolio, 
                start=start_date, 
                interval="1d"
            )

            # Procesar el DataFrame de yfinance
            daily_portfolio_values = [0.0] * num_days
            
            if not hist_data.empty:
                # Obtener solo los precios de Cierre 'Close'
                prices_df = hist_data['Close'].tail(num_days)

                for symbol in symbols_in_portfolio:
                    quantity = quantity_map[symbol]
                    
                    # Obtener la serie de precios para este símbolo
                    # Si hay un solo símbolo, la estructura del df es diferente
                    price_series = prices_df[symbol] if isinstance(prices_df, pd.DataFrame) else prices_df
                    
                    if price_series.empty:
                        # Fallback: usar el precio actual si no hay histórico
                        current_price = [item['current_price'] for item in portafolio_data if item['symbol'] == symbol][0]
                        asset_daily_values = [current_price * quantity] * num_days
                    else:
                        asset_daily_values = (price_series * quantity).tolist()
                        
                        # Rellenar días faltantes (si yf no devuelve 7 días)
                        if len(asset_daily_values) < num_days:
                            missing_days = num_days - len(asset_daily_values)
                            asset_daily_values = ([asset_daily_values[0]] * missing_days) + asset_daily_values

                    # Sumar los valores de este activo al total diario
                    for i in range(num_days):
                        daily_portfolio_values[i] += asset_daily_values[i]

            # --- Paso 3 (Refactorizado): Combinar con capital ---
            portfolio_history["values"] = [
                round(current_capital + daily_value, 2) for daily_value in daily_portfolio_values
            ]

        except Exception as e:
            print(f"ERROR: Fallo al obtener datos históricos para el gráfico: {e}")
            # Fallback: si la API falla, mostrar solo el capital
            portfolio_history["values"] = [round(current_capital, 2)] * num_days

    # --- Renderizar Plantilla ---
    return render_template(
        'Dashboard/dashboard.html',
        current_capital=current_capital,
        valor_portafolio=valor_portafolio,
        total_capital=total_capital,
        portafolio=portafolio_data,
        portfolio_history=portfolio_history
    )