from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.services.market_api import fetch_live_market_data, get_historical_data
from app.utils import MARKET_UNIVERSE 
from app.models import Holding, db
from datetime import datetime
import time
import yfinance as yf

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
    """
    Página de detalles históricos de un activo específico
    """
    try:
        # Buscar el activo en el universo de mercado
        asset_info = None
        for asset in MARKET_UNIVERSE:
            if asset['symbol'] == symbol:
                asset_info = asset
                break
        
        if not asset_info:
            flash(f'Activo {symbol} no encontrado.', 'danger')
            return redirect(url_for('market.market'))

        # Obtener datos históricos extensos para el gráfico detallado
        ticker = yf.Ticker(symbol)
        
        # Datos para diferentes periodos
        historical_data = {
            '1D': ticker.history(period='1d', interval='5m'),
            '1S': ticker.history(period='5d', interval='1h'),
            '1M': ticker.history(period='1mo', interval='1d'),
            '6M': ticker.history(period='6mo', interval='1d'),
            '1A': ticker.history(period='1y', interval='1d'),
            '5A': ticker.history(period='5y', interval='1wk')
        }
        
        # Procesar datos para cada periodo
        processed_data = {}
        for period, data in historical_data.items():
            if not data.empty:
                processed_data[period] = [
                    {
                        'time': index.strftime('%Y-%m-%d %H:%M:%S'),
                        'price': float(row['Close'])
                    }
                    for index, row in data.iterrows()
                ]
        
        # Información general del activo
        info = ticker.info
        asset_details = {
            'name': asset_info['name'],
            'symbol': symbol,
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'description': info.get('longBusinessSummary', 'Sin descripción disponible.'),
            'current_price': info.get('currentPrice', 0),
            'previous_close': info.get('previousClose', 0)
        }
        
        return render_template(
            'Market/asset_detail.html',
            asset=asset_details,
            historical_data=processed_data
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