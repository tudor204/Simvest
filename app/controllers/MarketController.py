from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Holding, User # Asegúrate de que estos modelos existan
from datetime import datetime
import yfinance as yf # Librería para datos de mercado en tiempo real
import time # Para la gestión del caché

# Definir el Blueprint
market_bp = Blueprint('market', __name__, url_prefix='/market')

# --- CONFIGURACIÓN DEL MERCADO Y CACHÉ ---

# Define el "Universo" de Productos que Simvest va a ofrecer.
# Usamos símbolos que yfinance entiende. Los bonos/renta fija se simulan con ETFs de bonos.
MARKET_UNIVERSE = [
    {'name': 'Vanguard S&P 500 ETF', 'symbol': 'VOO', 'category': 'etfs'},
    {'name': 'iShares Russell 2000 ETF', 'symbol': 'IWM', 'category': 'etfs'},
    {'name': 'Fidelity 500 Index Fund', 'symbol': 'FXAIX', 'category': 'fondos'},
    {'name': 'T. Rowe Price Blue Chip', 'symbol': 'TRBCX', 'category': 'fondos'},
    {'name': 'iShares 20+ Year Treasury Bond ETF', 'symbol': 'TLT', 'category': 'bonos'},
    {'name': 'Vanguard Total Bond Market ETF', 'symbol': 'BND', 'category': 'renta-fija'},
    {'name': 'Bitcoin', 'symbol': 'BTC-USD', 'category': 'crypto'},
    {'name': 'Ethereum', 'symbol': 'ETH-USD', 'category': 'crypto'},
    {'name': 'Apple Inc.', 'symbol': 'AAPL', 'category': 'acciones'},
    {'name': 'Tesla Inc.', 'symbol': 'TSLA', 'category': 'acciones'},
    {'name': 'Alphabet Inc. (Google)', 'symbol': 'GOOGL', 'category': 'acciones'},
    {'name': 'Amazon.com, Inc.', 'symbol': 'AMZN', 'category': 'acciones'}
]

# Estructura global para almacenar los datos del mercado en caché
market_data_cache = {
    "list": [],
    "dict": {},
    "timestamp": 0
}
CACHE_DURATION_SECONDS = 300 # 5 minutos para refrescar los datos

def get_market_data():
    """
    Obtiene datos de mercado de yfinance. Utiliza un caché de 5 minutos 
    para limitar las llamadas a la API y mejorar el rendimiento.
    Devuelve (product_list, product_dict)
    """
    global market_data_cache
    current_time = time.time()

    # Comprobar si la caché es válida (menos de 5 minutos)
    if current_time - market_data_cache["timestamp"] < CACHE_DURATION_SECONDS:
        return market_data_cache["list"], market_data_cache["dict"]

    # Cache obsoleta. Llamar a la API.
    symbols = [p['symbol'] for p in MARKET_UNIVERSE]
    
    # ⚠️ Manejo de errores básico para la conexión
    try:
        data = yf.Tickers(' '.join(symbols))
    except Exception as e:
        # Si la conexión falla, devolver la caché antigua si existe, o una lista vacía
        print(f"Error de conexión con yfinance: {e}. Devolviendo caché antigua.")
        return market_data_cache["list"], market_data_cache["dict"]

    product_list = []
    product_dict = {}

    for p_base in MARKET_UNIVERSE:
        symbol = p_base['symbol']
        try:
            ticker_data = data.tickers[symbol]
            
            # Intenta obtener el precio de cierre más reciente
            price = ticker_data.fast_info.get('lastPrice') or ticker_data.info.get('regularMarketPrice')
            previous_close = ticker_data.fast_info.get('previousClose') or ticker_data.info.get('regularMarketPreviousClose')

            if price is None or previous_close is None:
                 # Fallback usando el historial si fast_info falla (común en criptos o bonos)
                hist = ticker_data.history(period="1d", interval="5m")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    previous_close = ticker_data.history(period="2d", interval="1d")['Close'].iloc[-2]

            if price is None or previous_close is None:
                # Caso final de fallo, usar 0 o precio de la información estática
                price = 0.0
                previous_close = 0.0

            # Calcular cambio porcentual
            if previous_close == 0 or price == 0:
                change_pct = 0
            else:
                change_pct = ((price - previous_close) / previous_close) * 100
            
            change_str = f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"

            # Construir el producto final
            new_product = {
                'name': p_base['name'],
                'symbol': symbol,
                'price': price,
                'category': p_base['category'],
                'change': change_str
            }
            
            product_list.append(new_product)
            product_dict[symbol] = new_product
        
        except Exception as e:
            print(f"Error al procesar datos para {symbol}: {e}")
            fallback_product = {
                **p_base,
                'price': 0.00,
                'change': 'Error'
            }
            product_list.append(fallback_product)
            product_dict[symbol] = fallback_product

    # Actualizar la caché global
    market_data_cache["list"] = product_list
    market_data_cache["dict"] = product_dict
    market_data_cache["timestamp"] = current_time
    
    return product_list, product_dict


# --- RUTAS ---

@market_bp.route('/', methods=['GET', 'POST'])
@login_required
def market():
    
    # Obtener los datos más recientes del mercado (usando caché)
    try:
        products_list, products_dict = get_market_data()
    except Exception as e:
        flash(f'Error grave al obtener datos del mercado: {e}', 'danger')
        products_list = []
        products_dict = {}

    # ----------------------------------------------------
    # Lógica de Compra (POST)
    # ----------------------------------------------------
    if request.method == 'POST':
        symbol = request.form.get('symbol').upper()
        
        try:
            quantity = float(request.form.get('quantity'))
            if quantity <= 0:
                raise ValueError("La cantidad debe ser positiva.")
        except (TypeError, ValueError, AttributeError):
            flash('La cantidad debe ser un número positivo.', 'danger')
            return redirect(url_for('market.market'))

        # 1. Validar que el activo existe y tiene precio
        if symbol not in products_dict or products_dict[symbol]['price'] <= 0:
            flash(f'Activo {symbol} no disponible o sin precio de cotización.', 'danger')
            return redirect(url_for('market.market'))

        asset_info = products_dict[symbol]
        price_per_share = asset_info['price']
        total_cost = quantity * price_per_share
        
        # 2. Validación de Capital
        if total_cost > current_user.capital:
            flash('Capital insuficiente para realizar esta compra.', 'danger')
            return redirect(url_for('market.market'))
        
        # 3. Registrar la compra
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

    # ----------------------------------------------------
    # Renderizar la página (GET)
    # ----------------------------------------------------
    return render_template(
        'Market/market.html', # Asegúrate de que este es el nombre correcto del template
        products=products_list, 
        current_capital=f"{current_user.capital:,.2f}"
    )

# --- Ruta para procesar la Venta de Activos ---
# --- Ruta para procesar la Venta de Activos ---
@market_bp.route('/sell', methods=['POST'])
@login_required
def sell():
    
    # Obtener la cotización actual para la venta
    try:
        _, products_dict = get_market_data()
    except Exception:
        flash('Error al obtener la cotización actual. Venta cancelada.', 'danger')
        return redirect(url_for('market.market'))  # ✅ Corregido

    holding_id = request.form.get('holding_id', type=int) 
    quantity_to_sell = request.form.get('quantity_to_sell', type=float)
    
    holding = Holding.query.filter_by(id=holding_id, user_id=current_user.id).first()

    if not holding:
        flash('Posición no encontrada.', 'danger')
        return redirect(url_for('market.market'))  # ✅ Corregido

    if quantity_to_sell is None or quantity_to_sell <= 0 or quantity_to_sell > holding.quantity:
        flash('Cantidad de venta no válida.', 'danger')
        return redirect(url_for('market.market'))  # ✅ Corregido

    # Usar el precio de la API/Caché para la venta
    if holding.symbol not in products_dict or products_dict[holding.symbol]['price'] <= 0:
        flash(f'No se pudo obtener el precio de venta actual para {holding.symbol}. Venta cancelada.', 'danger')
        return redirect(url_for('market.market'))  # ✅ Corregido
        
    current_price = products_dict[holding.symbol]['price']
    
    # Registrar la venta
    total_proceeds = quantity_to_sell * current_price
    current_user.capital += total_proceeds
    holding.quantity -= quantity_to_sell
    
    if holding.quantity < 0.00001:
        db.session.delete(holding) 
    
    db.session.commit()
    
    flash(f'Venta simulada exitosa: {quantity_to_sell:,.2f} {holding.symbol} por ${total_proceeds:,.2f}', 'success')
    return redirect(url_for('market.market'))  # ✅ Corregido

