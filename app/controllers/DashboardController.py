from flask import render_template
from flask_login import login_required, current_user
from app.services.market_api import get_current_quote 
from app import app
from app.models import Holding

@app.route('/home')
@login_required
def home():    
    # 1️⃣ Obtener todas las inversiones activas del usuario
    holdings = Holding.query.filter_by(user_id=current_user.id, is_sold=False).all()

    # 2️⃣ Calcular el valor actual del portafolio
    valor_portafolio = 0
    portafolio_data = []

    for h in holdings:
        current_price = get_current_quote(h.symbol)  # Obtener cotización actual simulada
        gain_loss = (current_price - h.purchase_price) * h.quantity
        percent_change = ((current_price - h.purchase_price) / h.purchase_price) * 100 if h.purchase_price > 0 else 0

        valor_portafolio += current_price * h.quantity

        # Crear un diccionario con los datos necesarios para la tabla
        portafolio_data.append({
            'id': h.id,
            'symbol': h.symbol,
            'name': h.name,
            'quantity': h.quantity,
            'purchase_price': h.purchase_price,
            'current_price': current_price,
            'gain_loss': gain_loss,
            'percent_change': percent_change,
            'is_sold': h.is_sold
        })

    # 3️⃣ Calcular totales
    current_capital = current_user.capital
    total_capital = current_capital + valor_portafolio

    # 4️⃣ Renderizar la plantilla con todos los datos necesarios
    return render_template(
        'Home/home.html',
       current_capital=f"{current_user.capital:,.2f}",
        valor_portafolio=f"{valor_portafolio:,.2f}",
        total_capital=f"{total_capital:,.2f}",
        portafolio=portafolio_data
    )