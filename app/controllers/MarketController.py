from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

# Servicios del mercado y utilidades que centralizan toda la lógica externa
from app.market_service import (
    fetch_live_market_data, 
    fetch_historical_data, 
    fetch_single_asset_details, 
    get_asset_details
)

from app.utils.utils import MARKET_UNIVERSE 

# Modelos principales usados en operaciones del mercado
from app.models import Holding, db, Transaction, User

from datetime import datetime
import time
import yfinance as yf

# Blueprint para las rutas relacionadas con el mercado y las operaciones
market_bp = Blueprint('market', __name__, url_prefix='/market')


@market_bp.route('/', methods=['GET'])
@login_required
def market():
    # Renderizo la página principal del mercado con la lista de activos disponibles.
    return render_template(
        'Market/market.html',
        market_universe=MARKET_UNIVERSE
    )


@market_bp.route('/data/live', methods=['GET'])
@login_required
def get_live_market_data():
    # Devuelve una lista reducida de precios en vivo para actualizar el frontend.
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
    # Vista con la información completa del activo, incluyendo si el usuario lo posee.
    try:
        # Busco la info base del activo desde el universo del mercado.
        asset_info = next((a for a in MARKET_UNIVERSE if a['symbol'] == symbol), None)
        if not asset_info:
            flash(f'Activo {symbol} no encontrado.', 'danger')
            return redirect(url_for('market.market'))

        # Obtengo detalles en tiempo real según su categoría.
        asset_details = get_asset_details(symbol, asset_info['category'])
        if not asset_details:
            flash(f'Error al cargar datos para {symbol}.', 'danger')
            return redirect(url_for('market.market'))
        
        # Verifico si el usuario tiene posiciones en este activo.
        user_holding = Holding.query.filter_by(user_id=current_user.id, symbol=symbol).first()
        
        # Historial solo de este activo para el usuario.
        user_history = Transaction.query.filter_by(
            user_id=current_user.id,
            symbol=symbol
        ).order_by(Transaction.timestamp.desc()).limit(10).all()

        return render_template(
            'Market/asset_detail.html',
            asset=asset_details,
            holding=user_holding,
            history=user_history
        )
        
    except Exception as e:
        flash(f'Error al cargar datos para {symbol}: {str(e)}', 'danger')
        return redirect(url_for('market.market'))


@market_bp.route('/asset/<string:symbol>/history/<string:period>')
@login_required
def load_asset_historical_data(symbol, period):
    # Carga histórica bajo demanda, útil para no saturar el dashboard.
    try:
        start_time = time.time()
        data = fetch_historical_data(symbol, period)
        load_time = time.time() - start_time

        print(f"Datos {period} para {symbol} cargados en {load_time:.2f}s")
        
        if data:
            return jsonify(data)
        else:
            return jsonify({'error': 'No se pudieron cargar los datos históricos'}), 500
            
    except Exception as e:
        print(f"Error cargando datos históricos para {symbol} ({period}): {e}")
        return jsonify({'error': str(e)}), 500


@market_bp.route('/buy', methods=['POST'])
@login_required
def buy():
    # Ruta que gestiona compras tanto por monto como por unidades.
    symbol = request.form.get('symbol', '').upper()
    
    # Intento obtener el precio actual en vivo.
    try:
        asset_details = fetch_single_asset_details(symbol)
    except Exception:
        flash('Error al obtener la cotización actual. Compra cancelada.', 'danger')
        return redirect(url_for('market.asset_detail', symbol=symbol) or url_for('market.market'))

    # Validación básica del activo y del precio.
    if not asset_details or asset_details['price'] <= 0:
        flash(f'Activo {symbol} no disponible o sin precio válido.', 'danger')
        return redirect(url_for('market.asset_detail', symbol=symbol) or url_for('market.market'))
    
    price_per_unit = asset_details['price']
    asset_name = asset_details['name']
    
    # Aquí permito dos formas de compra: por unidades o por capital invertido.
    quantity = 0.0
    total_cost = 0.0
    
    quantity_input = request.form.get('quantity')
    amount_to_buy_input = request.form.get('amount_to_buy')
    
    try:
        if amount_to_buy_input:
            # Compra basada en capital disponible a invertir.
            amount_to_buy = float(amount_to_buy_input)
            if amount_to_buy <= 0:
                raise ValueError("El monto debe ser positivo.")
            
            total_cost = amount_to_buy
            quantity = amount_to_buy / price_per_unit
        
        elif quantity_input:
            # Compra clásica por número de unidades.
            quantity = float(quantity_input)
            if quantity <= 0:
                raise ValueError("La cantidad debe ser positiva.")

            total_cost = quantity * price_per_unit
        
        else:
            raise ValueError("Debes indicar la cantidad o el monto a invertir.")

    except (TypeError, ValueError) as e:
        flash(f'Entrada no válida: {e}', 'danger')
        return redirect(url_for('market.asset_detail', symbol=symbol) or url_for('market.market'))

    # Verifico que el usuario tenga capital suficiente.
    if total_cost > current_user.capital:
        flash(
            f'Capital insuficiente. Necesitas ${total_cost:,.2f} y solo tienes ${current_user.capital:,.2f}.',
            'danger'
        )
        return redirect(url_for('market.asset_detail', symbol=symbol) or url_for('market.market'))
    
    # Busco si ya existe un holding para sumar cantidades y actualizar el precio promedio.
    holding = Holding.query.filter_by(symbol=symbol, user_id=current_user.id).first()

    if holding:
        # Actualizo el precio promedio del holding si ya existía.
        current_total_value = holding.quantity * holding.purchase_price
        new_total_value = current_total_value + total_cost
        new_quantity = holding.quantity + quantity
        
        holding.purchase_price = new_total_value / new_quantity
        holding.quantity = new_quantity
        holding.purchase_date = datetime.utcnow()
        
    else:
        # Creo el holding desde cero si es la primera vez.
        holding = Holding(
            user_id=current_user.id,
            symbol=symbol,
            name=asset_name,
            quantity=quantity,
            purchase_price=price_per_unit,
            purchase_date=datetime.utcnow()
        )
        db.session.add(holding)
        
    # Descuento el capital invertido del usuario.
    current_user.capital -= total_cost
    
    # Registro formal de la transacción.
    new_transaction = Transaction(
        user_id=current_user.id,
        symbol=symbol,
        type='BUY',
        quantity=quantity,
        price_per_unit=price_per_unit,
        total_amount=total_cost
    )
    db.session.add(new_transaction)
    
    db.session.commit()
    
    flash(f'Compra exitosa: {quantity:,.4f} {symbol} por ${total_cost:,.2f}', 'success')
    return redirect(url_for('dashboard.dashboard'))


@market_bp.route('/sell', methods=['POST'])
@login_required
def sell():
    # Proceso de venta de un activo perteneciente al usuario.
    holding_id = request.form.get('holding_id', type=int)
    quantity_to_sell = request.form.get('quantity_to_sell', type=float)
    
    # Obtengo precios actuales de todos los activos monitoreados.
    try:
        _, products_dict = fetch_live_market_data()
    except Exception:
        db.session.rollback()
        flash('Error al obtener la cotización actual. Venta cancelada.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    # Verifico que el usuario realmente tenga este holding.
    holding = Holding.query.filter_by(id=holding_id, user_id=current_user.id).first()

    if not holding:
        flash('No se encontró la posición seleccionada.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    # Valido la cantidad a vender.
    if not quantity_to_sell or quantity_to_sell <= 0:
        flash('La cantidad a vender debe ser positiva.', 'danger')
        return redirect(url_for('dashboard.dashboard'))
        
    if quantity_to_sell > holding.quantity:
        flash(f'Solo tienes {holding.quantity:,.4f} unidades para vender.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    # Verifico que exista precio de venta disponible.
    if holding.symbol not in products_dict or products_dict[holding.symbol]['price'] <= 0:
        flash(f'No se pudo obtener un precio válido para {holding.symbol}.', 'danger')
        return redirect(url_for('dashboard.dashboard'))
        
    current_price = products_dict[holding.symbol]['price']
    
    # Cálculo del dinero recibido por la venta.
    total_proceeds = quantity_to_sell * current_price
    
    # Actualizo capital y cantidades del holding.
    current_user.capital += total_proceeds
    holding.quantity -= quantity_to_sell
    
    # Registro de la transacción SELL.
    new_transaction = Transaction(
        user_id=current_user.id,
        symbol=holding.symbol,
        type='SELL',
        quantity=quantity_to_sell,
        price_per_unit=current_price,
        total_amount=total_proceeds
    )
    db.session.add(new_transaction)
    
    # Elimino el holding si ya quedó prácticamente vacío.
    if holding.quantity < 0.00001:
        db.session.delete(holding)
    
    db.session.commit()
    
    flash(
        f'Venta realizada: {quantity_to_sell:,.4f} {holding.symbol} por ${total_proceeds:,.2f}', 
        'success'
    )
    return redirect(url_for('dashboard.dashboard'))
