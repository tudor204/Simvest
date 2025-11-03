from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.market_service import fetch_live_market_data, fetch_historical_data
from app.models import Holding
from datetime import datetime, timedelta

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

    # --- Paso 2: obtener valores históricos de los activos ---
    num_days = 7
    portfolio_daily_values = {}  # {symbol: [valor_por_dia,...]}

    for item in portafolio_data:  # Iterar sobre portafolio_data que SÍ tiene current_price
        symbol = item['symbol']
        current_price = item['current_price']
        quantity = item['quantity']
        
        historical_prices = fetch_historical_data(symbol, '1S')  # Última semana
        if not historical_prices or len(historical_prices) < num_days:
            # fallback: usamos precio actual desde portafolio_data
            portfolio_daily_values[symbol] = [current_price * quantity] * num_days
        else:
            # Tomamos solo los últimos `num_days` precios de cierre
            prices = [p['price'] for p in historical_prices[-num_days:]]
            portfolio_daily_values[symbol] = [p * quantity for p in prices]

    # --- Paso 3: combinar valores diarios para el gráfico ---
    portfolio_history = {"labels": [], "values": []}
    for i in range(num_days):
        day_label = (datetime.now() - timedelta(days=num_days - 1 - i)).strftime("%Y-%m-%d")
        portfolio_history["labels"].append(day_label)

        total_value = current_capital
        for values in portfolio_daily_values.values():
            total_value += values[i] if i < len(values) else values[-1]
        portfolio_history["values"].append(round(total_value, 2))

    return render_template(
        'Dashboard/dashboard.html',
        current_capital=current_capital,
        valor_portafolio=valor_portafolio,
        total_capital=total_capital,
        portafolio=portafolio_data,
        portfolio_history=portfolio_history
    )