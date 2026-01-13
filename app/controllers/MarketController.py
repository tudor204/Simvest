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
from app.models import Holding, db, Transaction, User, SimulationConfig

# Motor de simulación financiera
from app.domain import financial_engine
from app.domain.financial_engine import (
    InsufficientCapitalError,
    InsufficientHoldingsError,
    InvalidOperationError,
    validate_buy_order,
    validate_sell_order,
    calculate_portfolio_from_transactions,
    calculate_portfolio_metrics,
    generate_extended_buy_feedback,
    generate_extended_sell_feedback
)

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
    """
    Ruta de compra. Valida la orden mediante el motor de simulación,
    ejecuta la transacción, y proporciona feedback educativo.
    """
    symbol = request.form.get('symbol', '').upper()
    quantity_input = request.form.get('quantity')
    amount_to_buy_input = request.form.get('amount_to_buy')
    
    # Step 1: Obtener configuración y detalles del precio
    try:
        config = SimulationConfig.query.first() or SimulationConfig(
            initial_capital=10000.0,
            commission_rate=0.0005
        )
        
        asset_details = fetch_single_asset_details(symbol)
        if not asset_details or asset_details['price'] <= 0:
            raise InvalidOperationError(
                f"Activo {symbol} no disponible o sin precio válido"
            )
            
    except Exception as e:
        flash(f'Error al obtener datos: {str(e)}', 'danger')
        return redirect(url_for('market.asset_detail', symbol=symbol) or url_for('market.market'))
    
    price_per_unit = asset_details['price']
    asset_name = asset_details.get('name', symbol)
    
    # Step 2: Validar orden mediante engine
    try:
        quantity = float(quantity_input) if quantity_input else None
        amount_to_buy = float(amount_to_buy_input) if amount_to_buy_input else None
        
        final_quantity, total_cost = validate_buy_order(
            quantity=quantity,
            amount_to_buy=amount_to_buy,
            capital_available=current_user.capital,
            price_per_unit=price_per_unit,
            commission_rate=config.commission_rate,
            min_trade_amount=config.min_trade_amount
        )
        
    except (TypeError, ValueError) as e:
        flash(f'Entrada inválida: {str(e)}', 'danger')
        return redirect(url_for('market.asset_detail', symbol=symbol) or url_for('market.market'))
    
    except (InsufficientCapitalError, InvalidOperationError) as e:
        flash(f'❌ {str(e)}', 'danger')
        return redirect(url_for('market.asset_detail', symbol=symbol) or url_for('market.market'))
    
    # Step 3: Crear transacción en BD
    try:
        # Calcular comisión
        total_before_commission = final_quantity * price_per_unit
        commission_amount = total_before_commission * config.commission_rate
        
        # Crear Transaction
        new_transaction = Transaction(
            user_id=current_user.id,
            symbol=symbol,
            asset_name=asset_name,
            type='BUY',
            quantity=final_quantity,
            price_per_unit=price_per_unit,
            total_amount=total_before_commission,
            commission_amount=commission_amount,
            status='executed'
        )
        
        # Actualizar capital del usuario
        current_user.capital -= total_cost
        
        # Actualizar o crear holding (compatibilidad con vista existente)
        holding = Holding.query.filter_by(symbol=symbol, user_id=current_user.id).first()
        if holding:
            # Recalcular precio promedio
            current_total_value = holding.quantity * holding.purchase_price
            new_total_value = current_total_value + total_before_commission
            new_quantity = holding.quantity + final_quantity
            holding.purchase_price = new_total_value / new_quantity
            holding.quantity = new_quantity
            holding.purchase_date = datetime.utcnow()
        else:
            holding = Holding(
                user_id=current_user.id,
                symbol=symbol,
                name=asset_name,
                quantity=final_quantity,
                purchase_price=price_per_unit,
                purchase_date=datetime.utcnow()
            )
            db.session.add(holding)
        
        db.session.add(new_transaction)
        db.session.commit()
        
        # Step 4: Feedback educativo detallado
        current_prices = {symbol: price_per_unit}
        portfolio = financial_engine.calculate_portfolio_from_transactions(
            current_user.transactions,
            current_prices
        )
        portfolio_metrics = financial_engine.calculate_portfolio_metrics(
            portfolio,
            initial_capital=config.initial_capital
        )
        
        feedback = financial_engine.generate_extended_buy_feedback(
            symbol=symbol,
            quantity=final_quantity,
            price_per_unit=price_per_unit,
            total_cost=total_cost,
            commission_amount=commission_amount,
            portfolio=portfolio,
            portfolio_metrics=portfolio_metrics,
            initial_capital=config.initial_capital
        )
        
        # Mostrar feedback en múltiples líneas para máxima claridad
        flash_msg = f"[COMPRA] {feedback['summary']}", 'info'
        flash(f"[ASIGNACION] {feedback['allocation']}", 'warning' if 'ADVERTENCIA' in feedback['allocation'] else 'info')
        flash(f"[RIESGO] {feedback['risk']}", 'warning' if feedback['risk'].startswith('Riesgo del portfolio: ALTO') else 'info')
        flash(f"[SUGERENCIA] {feedback['suggestion']}", 'info')
        
        return redirect(url_for('dashboard.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar compra: {str(e)}', 'danger')
        return redirect(url_for('market.asset_detail', symbol=symbol) or url_for('market.market'))


@market_bp.route('/sell', methods=['POST'])
@login_required
def sell():
    """
    Ruta de venta. Valida la orden mediante el motor de simulación,
    ejecuta la transacción, y proporciona feedback educativo.
    """
    holding_id = request.form.get('holding_id', type=int)
    quantity_to_sell = request.form.get('quantity_to_sell', type=float)
    
    # Step 1: Validar entrada básica
    if not holding_id or not quantity_to_sell:
        flash('Entrada incompleta.', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    # Step 2: Obtener configuración y holding
    try:
        config = SimulationConfig.query.first() or SimulationConfig(
            initial_capital=10000.0,
            commission_rate=0.0005
        )
        
        holding = Holding.query.filter_by(id=holding_id, user_id=current_user.id).first()
        if not holding:
            flash('Posición no encontrada.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        
        # Obtener precio actual
        asset_details = fetch_single_asset_details(holding.symbol)
        if not asset_details or asset_details['price'] <= 0:
            raise InvalidOperationError(
                f"No se pudo obtener precio válido para {holding.symbol}"
            )
            
    except Exception as e:
        flash(f'Error al obtener datos: {str(e)}', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    price_per_unit = asset_details['price']
    
    # Step 3: Validar orden mediante engine
    try:
        final_quantity, total_proceeds = validate_sell_order(
            quantity_to_sell=quantity_to_sell,
            quantity_available=holding.quantity,
            price_per_unit=price_per_unit,
            commission_rate=config.commission_rate,
            min_trade_amount=config.min_trade_amount
        )
        
    except (InsufficientHoldingsError, InvalidOperationError) as e:
        flash(f'❌ {str(e)}', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    # Step 4: Crear transacción en BD
    try:
        # Calcular valores
        total_before_commission = final_quantity * price_per_unit
        commission_amount = total_before_commission * config.commission_rate
        
        # Crear Transaction
        new_transaction = Transaction(
            user_id=current_user.id,
            symbol=holding.symbol,
            asset_name=holding.name,
            type='SELL',
            quantity=final_quantity,
            price_per_unit=price_per_unit,
            total_amount=total_before_commission,
            commission_amount=commission_amount,
            status='executed'
        )
        
        # Actualizar capital del usuario
        current_user.capital += total_proceeds
        
        # Actualizar holding
        holding.quantity -= final_quantity
        
        # Eliminar si se vacía (evitar posiciones fantasma)
        if holding.quantity < 0.00001:
            db.session.delete(holding)
        
        db.session.add(new_transaction)
        db.session.commit()
        
        # Step 5: Feedback educativo detallado
        current_prices = {holding.symbol: price_per_unit}
        portfolio = financial_engine.calculate_portfolio_from_transactions(
            current_user.transactions,
            current_prices
        )
        portfolio_metrics = financial_engine.calculate_portfolio_metrics(
            portfolio,
            initial_capital=config.initial_capital
        )
        
        feedback = financial_engine.generate_extended_sell_feedback(
            symbol=holding.symbol,
            quantity=final_quantity,
            price_per_unit=price_per_unit,
            proceeds=total_proceeds,
            commission_amount=commission_amount,
            p_and_l_data=portfolio_metrics,
            portfolio=portfolio,
            portfolio_metrics=portfolio_metrics,
            initial_capital=config.initial_capital
        )
        
        # Mostrar feedback en múltiples líneas
        flash(f"[VENTA] {feedback['summary']}", 'info')
        flash(f"[RESULTADO] {feedback['performance']}", 'success' if portfolio_metrics['p_and_l_by_asset'].get(holding.symbol, {}).get('absolute', 0) > 0 else 'warning')
        flash(f"[ANALISIS] {feedback['insight']}", 'info')
        flash(f"[SUGERENCIA] {feedback['suggestion']}", 'info')
        
        return redirect(url_for('dashboard.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar venta: {str(e)}', 'danger')
        return redirect(url_for('dashboard.dashboard'))
