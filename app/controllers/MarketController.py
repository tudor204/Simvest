from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
# Importaciones de Servicios y Utilidades
from app.market_service import fetch_live_market_data, fetch_historical_data, fetch_single_asset_details, get_asset_details
from app.utils.utils import MARKET_UNIVERSE 
# Importaciones de Modelos
from app.models import Holding, db, Transaction, User
from datetime import datetime
import time
import yfinance as yf

# --- Definir Blueprint ---
market_bp = Blueprint('market', __name__, url_prefix='/market')



@market_bp.route('/', methods=['GET'])
@login_required
def market():
    """
    Ruta principal del mercado. Solo maneja la visualización de la lista de activos.
    (El método POST para compra ha sido movido a la ruta '/buy')
    """
    return render_template(
        'Market/market.html',
        market_universe=MARKET_UNIVERSE 
    )

@market_bp.route('/data/live', methods=['GET'])
@login_required
def get_live_market_data():
    """
    Devuelve datos de mercado en vivo (lista simplificada para el frontend)
    """
    try:
        products_list, _ = fetch_live_market_data()
        
        simplified_data = [
            {
                'symbol': p['symbol'], 
                'price': p['price'], 
                'change': p['change'],           
                'category': p.get('category', 'N/A'),
                'history': p.get('history', [])
            }
            for p in products_list
        ]
        
        return jsonify(simplified_data)
        
    except Exception as e:
        print(f"Error en la ruta /data/live: {e}")
        return jsonify({"error": "No se pudieron cargar los datos de cotización."}), 500

@market_bp.route('/asset/<string:symbol>')
@login_required
def asset_detail(symbol):
    """
    Página de detalles de un activo específico
    """
    try:
        # Buscar el activo en el universo de mercado
        asset_info = next((a for a in MARKET_UNIVERSE if a['symbol'] == symbol), None)
        if not asset_info:
            flash(f'Activo {symbol} no encontrado.', 'danger')
            return redirect(url_for('market.market'))

        # Usar la nueva función adaptada
        asset_details = get_asset_details(symbol, asset_info['category'])
        
        if not asset_details:
            flash(f'Error al cargar datos para {symbol}.', 'danger')
            return redirect(url_for('market.market'))
        
        return render_template('Market/asset_detail.html', asset=asset_details)
        
    except Exception as e:
        flash(f'Error al cargar datos para {symbol}: {str(e)}', 'danger')
        return redirect(url_for('market.market'))

@market_bp.route('/asset/<string:symbol>/history/<string:period>')
@login_required
def load_asset_historical_data(symbol, period):
    """
    Carga dinámica de datos históricos (solo al hacer clic en un periodo o activo)
    """
    try:
        start_time = time.time()
        data = fetch_historical_data(symbol, period)
        load_time = time.time() - start_time
        
        print(f"📊 Datos {period} para {symbol} cargados en {load_time:.2f}s")
        
        if data:
            return jsonify(data)
        else:
            return jsonify({'error': 'No se pudieron cargar los datos históricos'}), 500
            
    except Exception as e:
        print(f"❌ Error cargando datos históricos para {symbol} ({period}): {e}")
        return jsonify({'error': str(e)}), 500


@market_bp.route('/buy', methods=['POST'])
@login_required
def buy():
    """
    Maneja la lógica de la compra de un activo, permitiendo la compra por unidades (quantity)
    o por monto (amount_to_buy), y registra la Transacción.
    """
    symbol = request.form.get('symbol', '').upper()
    
    # 1. Obtener cotización actual (Necesario para calcular la cantidad/costo)
    try:
        asset_details = fetch_single_asset_details(symbol) 
    except Exception:
        flash('Error al obtener la cotización actual. Compra cancelada.', 'danger')
        return redirect(url_for('market.asset_detail', symbol=symbol) or url_for('market.market'))

    # 2. Validar precio y existencia del activo
    if not asset_details or asset_details['price'] <= 0:
        flash(f'Activo {symbol} no disponible o sin precio de cotización.', 'danger')
        return redirect(url_for('market.asset_detail', symbol=symbol) or url_for('market.market'))
    
    price_per_unit = asset_details['price']
    asset_name = asset_details['name']
    
    # 3. Determinar si la compra es por UNIDADES o por MONTO
    quantity = 0.0
    total_cost = 0.0
    
    quantity_input = request.form.get('quantity')
    amount_to_buy_input = request.form.get('amount_to_buy') # Campo que el usuario usará para comprar por capital
    
    try:
        if amount_to_buy_input:
            # Opción A: Compra por MONTO (Ej: Quiero comprar 500€ de este activo)
            amount_to_buy = float(amount_to_buy_input)
            if amount_to_buy <= 0:
                raise ValueError("El monto de compra debe ser un número positivo.")
            
            # El costo total es el monto que el usuario quiere invertir
            total_cost = amount_to_buy
            # La cantidad es la parte fraccional o entera calculada
            quantity = amount_to_buy / price_per_unit
            
        elif quantity_input:
            # Opción B: Compra por UNIDADES (Comportamiento original)
            quantity = float(quantity_input)
            if quantity <= 0:
                raise ValueError("La cantidad de unidades debe ser un número positivo.")
                
            # Cálculo del costo total
            total_cost = quantity * price_per_unit
            
        else:
            # Ningún campo de compra fue enviado
            raise ValueError("Debe especificar la cantidad de unidades o el monto de capital a invertir.")

    except (TypeError, ValueError) as e:
        flash(f'Entrada no válida: {e}', 'danger')
        return redirect(url_for('market.asset_detail', symbol=symbol) or url_for('market.market'))

    # 4. Validar Capital (Usa current_user.capital como solicitaste)
    if total_cost > current_user.capital:
        # Usa el capital del usuario para el mensaje de error
        flash(f'Capital insuficiente. Necesitas ${total_cost:,.2f} y solo tienes ${current_user.capital:,.2f}.', 'danger')
        return redirect(url_for('market.asset_detail', symbol=symbol) or url_for('market.market'))
    
    # 5. Buscar o Crear Holding y Recalcular Precio Promedio
    holding = Holding.query.filter_by(symbol=symbol, user_id=current_user.id).first()

    if holding:
        # 5a. ACTIVO EXISTENTE: Recalcular Precio Promedio Ponderado
        current_total_value = holding.quantity * holding.purchase_price
        new_total_value = current_total_value + total_cost
        new_quantity = holding.quantity + quantity
        
        holding.purchase_price = new_total_value / new_quantity
        holding.quantity = new_quantity
        holding.purchase_date = datetime.utcnow()
        
    else:
        # 5b. NUEVO ACTIVO: Crear un nuevo Holding
        holding = Holding(
            user_id=current_user.id,
            symbol=symbol,
            name=asset_name,
            quantity=quantity, # Cantidad (potencialmente fraccionaria) comprada
            purchase_price=price_per_unit,
            purchase_date=datetime.utcnow()
        )
        db.session.add(holding)
        
    # 6. Actualizar Capital
    current_user.capital -= total_cost
    
    # 7. REGISTRAR LA TRANSACCIÓN
    new_transaction = Transaction(
        user_id=current_user.id,
        symbol=symbol,
        type='BUY',
        quantity=quantity,
        price_per_unit=price_per_unit,
        total_amount=total_cost
    )
    db.session.add(new_transaction)
    
    # 8. Guardar todos los cambios
    db.session.commit()
    
    flash(f'Compra simulada exitosa: {quantity:,.4f} {symbol} por ${total_cost:,.2f}', 'success')
    return redirect(url_for('dashboard.dashboard'))


# =========================================================
# 💰 RUTA DE VENTA
# =========================================================
@market_bp.route('/sell', methods=['POST'])
@login_required
def sell():
    """
    Maneja la venta de un activo, actualizando el holding y registrando la Transacción.
    """
    # 1. Obtener datos del formulario
    holding_id = request.form.get('holding_id', type=int) 
    quantity_to_sell = request.form.get('quantity_to_sell', type=float)
    
    # 2. Obtener cotización actual
    try:
        _, products_dict = fetch_live_market_data() 
    except Exception:
        db.session.rollback()
        flash('Error al obtener la cotización actual. Venta cancelada.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    # 3. Validar Posición (Holding)
    holding = Holding.query.filter_by(id=holding_id, user_id=current_user.id).first()

    if not holding:
        flash('Posición no encontrada o no pertenece a tu cartera.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    # 4. Validar Cantidad
    if quantity_to_sell is None or quantity_to_sell <= 0:
        flash('La cantidad a vender debe ser un número positivo.', 'danger')
        return redirect(url_for('dashboard.dashboard'))
        
    if quantity_to_sell > holding.quantity:
        flash(f'Solo tienes {holding.quantity:,.4f} unidades de {holding.symbol} para vender.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    # 5. Validar Precio de Venta
    if holding.symbol not in products_dict or products_dict[holding.symbol]['price'] <= 0:
        flash(f'No se pudo obtener el precio de venta actual para {holding.symbol}. Venta cancelada.', 'danger')
        return redirect(url_for('dashboard.dashboard'))
        
    current_price = products_dict[holding.symbol]['price']
    
    # 6. Ejecutar la Venta (Actualización de Modelos)
    total_proceeds = quantity_to_sell * current_price
    
    # Aumentar el capital del usuario
    current_user.capital += total_proceeds
    
    # Disminuir la cantidad de la posición
    holding.quantity -= quantity_to_sell
    
    # 7. REGISTRAR LA TRANSACCIÓN
    new_transaction = Transaction(
        user_id=current_user.id,
        symbol=holding.symbol,
        type='SELL',
        quantity=quantity_to_sell,
        price_per_unit=current_price,
        total_amount=total_proceeds 
    )
    db.session.add(new_transaction)
    
    # 8. Limpiar Posición si es residual
    if holding.quantity < 0.00001:
        db.session.delete(holding) 
    
    # 9. Guardar todos los cambios
    db.session.commit()
    
    flash(f'Venta simulada exitosa: {quantity_to_sell:,.4f} {holding.symbol} vendidas por ${total_proceeds:,.2f}', 'success')
    return redirect(url_for('dashboard.dashboard'))