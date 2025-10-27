from flask import Blueprint, render_template
from flask_login import login_required, current_user
# 💡 IMPORTACIÓN CORREGIDA: Asumiendo que has movido get_market_data a services
# Si la dejaste en un blueprint, ajusta la importación (ej: from ..market.market_bp import get_market_data)
from app.services.market_api import fetch_live_market_data
from app.models import Holding
from datetime import datetime, timedelta

# --- Definir Blueprint ---
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def dashboard():
    # Obtener todas las inversiones activas del usuario
    holdings = Holding.query.filter_by(user_id=current_user.id, is_sold=False).all()

    # 1. OBTENER TODOS LOS DATOS DEL MERCADO UNA SOLA VEZ
    # get_market_data() devuelve una lista (ignorada) y un diccionario (products_dict)
    try:
        _, products_dict = fetch_live_market_data() 
    except Exception as e:
        # En caso de fallo de la API (rate limit, etc.), usamos un diccionario vacío
        print(f"ERROR: Fallo al obtener datos del mercado: {e}")
        products_dict = {}

    valor_portafolio = 0
    portafolio_data = []

    for h in holdings:
        symbol = h.symbol
        
        # 2. BUSCAR EL PRECIO EN EL DICCIONARIO
        # Usamos .get() para obtener la información de mercado del símbolo.
        market_info = products_dict.get(symbol, {})
        
        # 3. EXTRAER EL PRECIO con FALLBACK
        # Si el símbolo no se encuentra en el diccionario, usamos el precio de compra como fallback.
        current_price = market_info.get('price', h.purchase_price) 
        
        # Asegurarse que el precio es float
        try:
            current_price = float(current_price)
        except (TypeError, ValueError):
            current_price = h.purchase_price # Fallback final si la conversión falla

        # --- Cálculos de Portafolio ---
        gain_loss = (current_price - h.purchase_price) * h.quantity
        percent_change = ((current_price - h.purchase_price) / h.purchase_price) * 100 if h.purchase_price > 0 else 0

        valor_portafolio += current_price * h.quantity

        portafolio_data.append({
            'id': h.id,
            'symbol': h.symbol,
            # Asegúrate de obtener el nombre también si es posible, si no usa el que está guardado
            'name': market_info.get('name', h.name), 
            'quantity': h.quantity,
            'purchase_price': h.purchase_price,
            'current_price': current_price,
            'gain_loss': gain_loss,
            'percent_change': percent_change,
            'is_sold': h.is_sold
        })

    current_capital = float(current_user.capital)
    total_capital = current_capital + valor_portafolio

    # Generar histórico simulado del portafolio para el gráfico
    portfolio_history = {
        "labels": [],
        "values": []
    }
    for i in range(7, 0, -1):
        day = datetime.now() - timedelta(days=i)
        portfolio_history["labels"].append(day.strftime("%Y-%m-%d"))
        simulated_value = valor_portafolio * (1 + (i - 4) * 0.01)  
        portfolio_history["values"].append(round(simulated_value + current_capital, 2))

    return render_template(
        'Dashboard/dashboard.html',
        current_capital=current_capital,
        valor_portafolio=valor_portafolio,
        total_capital=total_capital,
        portafolio=portafolio_data,
        portfolio_history=portfolio_history
    )
