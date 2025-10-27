from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.services.market_api import fetch_live_market_data, get_asset_details, get_historical_data, preload_historical_data
from app.utils import MARKET_UNIVERSE 
from app.models import Holding, db
from datetime import datetime
import time

# --- Definir Blueprint ---
market_bp = Blueprint('market', __name__, url_prefix='/market')

@market_bp.route('/', methods=['GET', 'POST'])
@login_required
def market():
    if request.method == 'POST':
        try:
            _, products_dict = fetch_live_market_data()
        except Exception as e:
            flash(f'Error al obtener datos del mercado para la compra: {e}', 'danger')
            return redirect(url_for('market.market'))

        symbol = request.form.get('symbol').upper()
        
        try:
            quantity = float(request.form.get('quantity'))
            if quantity <= 0:
                raise ValueError("La cantidad debe ser positiva.")
        except (TypeError, ValueError, AttributeError):
            flash('La cantidad debe ser un número positivo.', 'danger')
            return redirect(url_for('market.market'))

        if symbol not in products_dict or products_dict[symbol]['price'] <= 0:
            flash(f'Activo {symbol} no disponible o sin precio de cotización.', 'danger')
            return redirect(url_for('market.market'))

        asset_info = products_dict[symbol]
        price_per_share = asset_info['price']
        total_cost = quantity * price_per_share
        
        if total_cost > current_user.capital:
            flash('Capital insuficiente para realizar esta compra.', 'danger')
            return redirect(url_for('market.market'))
        
        new_holding = Holding(
            user_id=current_user.id,
            symbol=symbol,
            name=asset_info['name'],
            quantity=quantity,
            purchase_price=price_per_share,
            purchase_date=datetime.utcnow()
        )
        current_user.capital -= total_cost
        
        db.session.add(new_holding)
        db.session.commit()
        
        flash(f'Compra simulada exitosa: {quantity} {symbol} por ${total_cost:,.2f}', 'success')
        return redirect(url_for('market.market'))

    return render_template(
        'Market/market.html',
        market_universe=MARKET_UNIVERSE 
    )

@market_bp.route('/data/live', methods=['GET'])
@login_required
def get_live_market_data():
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
    try:
        asset_info = next((asset for asset in MARKET_UNIVERSE if asset['symbol'] == symbol), None)
        
        if not asset_info:
            flash(f'Activo {symbol} no encontrado.', 'danger')
            return redirect(url_for('market.market'))

        start_time = time.time()
        asset_details = get_asset_details(symbol)
        asset_time = time.time() - start_time
        
        if not asset_details:
            flash(f'Error al cargar datos para {symbol}.', 'danger')
            return redirect(url_for('market.market'))

        combined_asset_info = {
            'name': asset_info['name'],
            'symbol': symbol,
            'sector': asset_details.get('sector', 'N/A'),
            'industry': asset_details.get('industry', 'N/A'),
            'market_cap': asset_details.get('market_cap', 'N/A'),
            'description': asset_details.get('description', 'Sin descripción disponible.'),
            'current_price': asset_details.get('current_price', 0),
            'previous_close': asset_details.get('previous_close', 0),
            'category': asset_info.get('category', 'N/A')
        }

        historical_data = {}
        initial_period = '1D'
        
        start_hist_time = time.time()
        hist_data = get_historical_data(symbol, initial_period)
        hist_time = time.time() - start_hist_time
        
        if hist_data:
            historical_data[initial_period] = hist_data
            print(f"🚀 Datos históricos cargados en {hist_time:.2f}s")

        preload_historical_data(symbol)

        total_time = time.time() - start_time
        print(f"⏱️  Página de detalles cargada en {total_time:.2f}s (asset: {asset_time:.2f}s, hist: {hist_time:.2f}s)")

        return render_template(
            'Market/asset_detail.html',
            asset=combined_asset_info,
            historical_data=historical_data
        )
        
    except Exception as e:
        flash(f'Error al cargar datos para {symbol}: {str(e)}', 'danger')
        return redirect(url_for('market.market'))

@market_bp.route('/asset/<string:symbol>/history/<string:period>')
@login_required
def load_asset_historical_data(symbol, period):
    try:
        start_time = time.time()
        data = get_historical_data(symbol, period)
        load_time = time.time() - start_time
        
        print(f"📊 Datos {period} para {symbol} cargados en {load_time:.2f}s")
        
        if data is not None:
            return jsonify(data)
        else:
            return jsonify({'error': 'No se pudieron cargar los datos históricos'}), 500
            
    except Exception as e:
        print(f"❌ Error cargando datos históricos para {symbol} ({period}): {e}")
        return jsonify({'error': str(e)}), 500

@market_bp.route('/sell', methods=['POST'])
@login_required
def sell():
    try:
        _, products_dict = fetch_live_market_data()
    except Exception:
        flash('Error al obtener la cotización actual. Venta cancelada.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    holding_id = request.form.get('holding_id', type=int) 
    quantity_to_sell = request.form.get('quantity_to_sell', type=float)
    
    holding = Holding.query.filter_by(id=holding_id, user_id=current_user.id).first()

    if not holding:
        flash('Posición no encontrada.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    if quantity_to_sell is None or quantity_to_sell <= 0 or quantity_to_sell > holding.quantity:
        flash('Cantidad de venta no válida.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    if holding.symbol not in products_dict or products_dict[holding.symbol]['price'] <= 0:
        flash(f'No se pudo obtener el precio de venta actual para {holding.symbol}. Venta cancelada.', 'danger')
        return redirect(url_for('dashboard.dashboard'))
        
    current_price = products_dict[holding.symbol]['price']
    
    total_proceeds = quantity_to_sell * current_price
    current_user.capital += total_proceeds
    holding.quantity -= quantity_to_sell
    
    if holding.quantity < 0.00001:
        db.session.delete(holding) 
    
    db.session.commit()
    
    flash(f'Venta simulada exitosa: {quantity_to_sell:,.2f} {holding.symbol} por ${total_proceeds:,.2f}', 'success')
    return redirect(url_for('dashboard.dashboard'))