from flask import render_template
from flask_login import login_required, current_user
from app.services.market_api import get_current_quote 
from app import app
from app.models import Holding
from datetime import datetime, timedelta

@app.route('/home')
@login_required
def home():    
    # Obtener todas las inversiones activas del usuario
    holdings = Holding.query.filter_by(user_id=current_user.id, is_sold=False).all()

    valor_portafolio = 0
    portafolio_data = []

    for h in holdings:
        current_price = float(get_current_quote(h.symbol))  # Asegurarse que sea float
        gain_loss = (current_price - h.purchase_price) * h.quantity
        percent_change = ((current_price - h.purchase_price) / h.purchase_price) * 100 if h.purchase_price > 0 else 0

        valor_portafolio += current_price * h.quantity

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

    current_capital = float(current_user.capital)
    total_capital = current_capital + valor_portafolio

    # Generar histórico simulado del portafolio para el gráfico
    portfolio_history = {
        "labels": [],
        "values": []
    }
    for i in range(7, 0, -1):  # Últimos 7 días
        day = datetime.now() - timedelta(days=i)
        portfolio_history["labels"].append(day.strftime("%Y-%m-%d"))
        # Simulación: valor_portafolio +/- pequeñas variaciones
        simulated_value = valor_portafolio * (1 + (i-4)*0.01)  # simple fluctuación
        portfolio_history["values"].append(round(simulated_value + current_capital, 2))

    return render_template(
        'Dashboard/dashboard.html',
        current_capital=current_capital,
        valor_portafolio=valor_portafolio,
        total_capital=total_capital,
        portafolio=portafolio_data,
        portfolio_history=portfolio_history
    )
