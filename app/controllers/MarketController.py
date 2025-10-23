# app/controllers/MarketController.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Holding, User
from datetime import datetime

# Definir el Blueprint
market_bp = Blueprint('market', __name__, url_prefix='/market')

# --- Ruta para mostrar el mercado y el formulario de compra ---
@market_bp.route('/', methods=['GET', 'POST'])
@login_required
def market():
    # ⚠️ Nota: En una aplicación real, aquí integrarías una API de mercado (ej. Alpha Vantage, Finnhub)
    # Para la simulación, usaremos datos fijos.
    
    # ----------------------------------------------------
    # Lógica de Compra (POST)
    # ----------------------------------------------------
    if request.method == 'POST':
        # Obtener datos del formulario de compra
        symbol = request.form.get('symbol').upper() # Símbolo de la acción, ej: AAPL
        quantity = float(request.form.get('quantity'))
        
        # Simulamos un precio de compra fijo (Para una app real, debe ser dinámico)
        # Aquí puedes cambiar los valores fijos para que el ejemplo funcione:
        asset_info = {
            'AAPL': {'name': 'Apple Inc.', 'price': 150.00},
            'TSLA': {'name': 'Tesla Inc.', 'price': 250.00}
        }

        if symbol not in asset_info:
            flash('Símbolo de acción no válido.', 'danger')
            return redirect(url_for('market.market'))

        price_per_share = asset_info[symbol]['price']
        total_cost = quantity * price_per_share
        
        # Validación de Capital
        if total_cost > current_user.capital:
            flash('Capital insuficiente para realizar esta compra.', 'danger')
        elif quantity <= 0:
            flash('La cantidad debe ser mayor que cero.', 'danger')
        else:
            # 1. Crear la nueva inversión (Holding)
            new_holding = Holding(
                user_id=current_user.id,
                symbol=symbol,
                name=asset_info[symbol]['name'],
                quantity=quantity,
                purchase_price=price_per_share,
                purchase_date=datetime.utcnow()
            )
            
            # 2. Actualizar el capital del usuario
            current_user.capital -= total_cost
            
            # 3. Guardar cambios en la base de datos
            db.session.add(new_holding)
            db.session.commit()
            
            flash(f'Compra simulada exitosa: {quantity} acciones de {symbol} por ${total_cost:,.2f}', 'success')
            return redirect(url_for('market.market')) # Redirigir para evitar reenvío de formulario

    # ----------------------------------------------------
    # Renderizar la página (GET)
    # ----------------------------------------------------
    # Datos simulados para mostrar en la tabla de cotizaciones
    simulated_quotes = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.', 'price': 150.00},
        {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'price': 250.00},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc. (Google)', 'price': 1200.00},
        {'symbol': 'AMZN', 'name': 'Amazon.com, Inc.', 'price': 130.00},
    ]

    return render_template(
        'Market/market.html', 
        quotes=simulated_quotes, 
        current_capital=f"{current_user.capital:,.2f}"
    )

# --- Ruta para procesar la Venta de Activos ---
@market_bp.route('/sell', methods=['POST'])
@login_required
def sell():
    # Obtener datos del formulario de venta (que crearemos en home.html)
    holding_id = request.form.get('holding_id', type=int) # ID del registro Holding que se va a vender
    quantity_to_sell = request.form.get('quantity_to_sell', type=float)
    
    # 1. Buscar la posición (Holding) del usuario
    holding = Holding.query.filter_by(id=holding_id, user_id=current_user.id).first()

    if not holding:
        flash('Posición no encontrada o no te pertenece.', 'danger')
        return redirect(url_for('home')) # Redirigir al dashboard

    if quantity_to_sell <= 0 or quantity_to_sell > holding.quantity:
        flash('Cantidad de venta no válida.', 'danger')
        return redirect(url_for('home'))

    # 2. Obtener el precio actual (usando nuestro simulador de API)
    # Importante: Esto garantiza que la venta se haga a la cotización "real" simulada.
    from app.services.market_api import get_current_quote 
    current_price = get_current_quote(holding.symbol)
    
    # 3. Calcular la ganancia de la transacción
    total_proceeds = quantity_to_sell * current_price
    
    # 4. Actualizar el capital del usuario (Añadir el dinero de la venta)
    current_user.capital += total_proceeds
    
    # 5. Actualizar la posición (Holding)
    holding.quantity -= quantity_to_sell
    
    # Si la posición queda a cero, la marcamos como vendida (is_sold = True)
    if holding.quantity <= 0.0001: # Usamos un valor pequeño por seguridad con floats
        holding.quantity = 0.0
        holding.is_sold = True # Marcar como completamente vendida

    # 6. Guardar la transacción
    db.session.commit()
    
    flash(f'Venta simulada exitosa: {quantity_to_sell:,.2f} acciones de {holding.symbol} por ${total_proceeds:,.2f}', 'success')
    return redirect(url_for('home'))