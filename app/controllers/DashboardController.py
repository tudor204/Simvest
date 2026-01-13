from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models import Holding, Transaction, SimulationConfig
from sqlalchemy import desc
from datetime import datetime, timedelta
import yfinance as yf
import time
import concurrent.futures
from app import cache

# Motor de simulación financiera con métricas
from app.domain import financial_engine

# Blueprint del dashboard: aquí centralizo todo lo que muestra datos del portafolio.
from app.market_service import get_simple_chart_data, get_portfolio_historical_value

# Caché para precios de activos
price_cache = {}
CACHE_DURATION = 600  # 10 minutos

def get_cached_price(symbol):
    """Obtiene precio con caché para evitar llamadas repetidas a yfinance"""
    now = time.time()
    if symbol in price_cache and now - price_cache[symbol]['timestamp'] < CACHE_DURATION:
        return price_cache[symbol]['price']
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('navPrice')
        if price:
            price_cache[symbol] = {'price': float(price), 'timestamp': now}
            return float(price)
    except Exception as e:
        print(f"Error obteniendo precio para {symbol}: {e}")
    
    return 0.0

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def make_dashboard_cache_key():
    return f"dashboard_data_{current_user.id}_{request.args.get('timeframe', 'Todo')}"

def get_dashboard_data(user, timeframe='TODO'):
    """Función helper para calcular datos del dashboard"""
    timeframe = timeframe.upper()
    
    holdings = Holding.query.filter_by(user_id=user.id).all()
    
    # Si no tiene inversiones, devuelvo un gráfico vacío pero coherente.
    if not holdings:
        chart_data = get_simple_chart_data(float(user.capital), timeframe=timeframe)
        return {
            'summary': {
                'portfolio_value': 0,
                'total_capital': float(user.capital),
                'pnl': 0,
                'pnl_pct': 0
            },
            'holdings_updates': {},
            'chart_data': chart_data
        }

    # Solo descargo precios de los símbolos que realmente tiene el usuario.
    symbols = [h.symbol for h in holdings]
    live_prices = {}

    # Usar paralelismo para obtener precios más rápido
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_symbol = {executor.submit(get_cached_price, symbol): symbol for symbol in symbols}
        for future in concurrent.futures.as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                live_prices[symbol] = future.result()
            except Exception as e:
                print(f"Error obteniendo precio para {symbol}: {e}")
                live_prices[symbol] = 0.0

    # ==========================
    # Cálculo de valores
    # ==========================
    valor_portafolio = 0
    total_invested = 0
    holdings_updates = {}

    for h in holdings:
        # Si yfinance falla, uso el precio de compra como plan B.
        current_price = live_prices.get(h.symbol, h.purchase_price)
        if current_price <= 0:
            current_price = h.purchase_price

        current_val = current_price * h.quantity
        invested_val = h.purchase_price * h.quantity
        
        valor_portafolio += current_val
        total_invested += invested_val

        gain = current_val - invested_val
        pct = (gain / invested_val * 100) if invested_val > 0 else 0

        # Datos que actualizarán la tabla del frontend en tiempo real.
        holdings_updates[h.id] = {
            'current_price': current_price,
            'total_value': current_val,
            'gain': gain,
            'pct': pct
        }

    # ==========================
    # Totales globales
    # ==========================
    current_capital = float(user.capital)
    total_capital = current_capital + valor_portafolio

    # Capital inicial fijo (podrías hacerlo configurable luego).
    initial_capital = 10000.00
    overall_pnl = total_capital - initial_capital
    overall_pnl_pct = (overall_pnl / initial_capital * 100) if initial_capital > 0 else 0

    # ==========================
    # Gráfico (usa timeframe)
    # ==========================
    # Si tienes implementado el histórico real del portafolio, aquí se usaría.
    # chart_data = get_portfolio_historical_value(holdings, current_capital, timeframe)

    # Por ahora usamos la función simple para que siempre funcione.
    chart_data = get_simple_chart_data(total_capital, timeframe=timeframe)

    return {
        'summary': {
            'portfolio_value': valor_portafolio,
            'total_capital': total_capital,
            'pnl': overall_pnl,
            'pnl_pct': overall_pnl_pct
        },
        'holdings_updates': holdings_updates,
        'chart_data': chart_data
    }

# ================================
# DASHBOARD PRINCIPAL (solo BD)
# ================================
@dashboard_bp.route('/')
@login_required
def dashboard():
    """
    Dashboard principal con métricas enriquecidas (FASE 3).
    
    Muestra:
    - Portfolio actual (valor total, cash, invertido)
    - Métricas avanzadas (drawdown, volatilidad, Sharpe)
    - Riesgo y asignación
    - Detalles de holdings con P&L individual
    """
    # Obtener configuración
    config = SimulationConfig.query.first() or SimulationConfig()
    
    # Generar datos enriquecidos del dashboard
    try:
        dashboard_data = financial_engine.generate_dashboard_data(current_user, config)
        print(f"Dashboard data generated: {bool(dashboard_data)} keys: {list(dashboard_data.keys()) if dashboard_data else 'None'}")
    except Exception as e:
        print(f"Error generando dashboard data: {e}")
        import traceback
        traceback.print_exc()
        dashboard_data = {}
    
    # Último movimiento
    latest_transaction = Transaction.query.filter_by(user_id=current_user.id)\
                                          .order_by(desc(Transaction.timestamp))\
                                          .first()
    
    # Histórico reciente (últimas 5)
    transaction_history = Transaction.query.filter_by(user_id=current_user.id)\
                                           .order_by(desc(Transaction.timestamp))\
                                           .limit(5).all()
    
    # Data inicial para JavaScript (compatible con updateUI)
    # Necesitamos crear la estructura que espera el JavaScript
    from app.market_service import get_simple_chart_data
    
    # Crear datos iniciales en formato API
    initial_api_data = {
        'summary': {
            'portfolio_value': dashboard_data.get('portfolio', {}).get('total_invested', 0),
            'total_capital': dashboard_data.get('portfolio', {}).get('total_portfolio_value', current_user.capital),
            'pnl': dashboard_data.get('metrics', {}).get('total_p_and_l', 0),
            'pnl_pct': dashboard_data.get('metrics', {}).get('total_return_pct', 0)
        },
        'holdings_updates': {},
        'chart_data': get_simple_chart_data(float(dashboard_data.get('portfolio', {}).get('total_portfolio_value', current_user.capital)))
    }
    
    # Si hay holdings, agregar holdings_updates
    if dashboard_data.get('holdings_detail'):
        for holding in dashboard_data['holdings_detail']:
            holding_id = f"holding_{holding['symbol']}"  # Crear ID único
            initial_api_data['holdings_updates'][holding_id] = {
                'current_price': holding['current_price'],
                'total_value': holding['current_value'],
                'gain': holding['p_and_l_absolute'],
                'pct': holding['p_and_l_pct']
            }
    
    # Data simple para compatibilidad
    initial_data = {
        'portfolio_value': dashboard_data.get('portfolio', {}).get('total_portfolio_value', 0),
        'cash': dashboard_data.get('portfolio', {}).get('cash_available', 0),
        'total_return_pct': dashboard_data.get('metrics', {}).get('total_return_pct', 0),
        'has_data': bool(dashboard_data and dashboard_data.get('portfolio'))
    }
    
    return render_template(
        'Dashboard/dashboard.html',
        dashboard_data=dashboard_data,
        initial_api_data=initial_api_data,
        initial_data=initial_data,
        latest_transaction=latest_transaction,
        transaction_history=transaction_history,
        current_capital=current_user.capital,
        config=config
    )

# ==================================
# ENDPOINT PARA DATOS EN VIVO
# ==================================
@dashboard_bp.route('/api/data')
@login_required
@cache.cached(timeout=300, make_cache_key=make_dashboard_cache_key)
def dashboard_data():
    # Obtengo el timeframe del gráfico que pide el usuario.
    timeframe = request.args.get('timeframe', 'Todo').upper()
    
    try:
        data = get_dashboard_data(current_user, timeframe)
        return jsonify(data)
    except Exception as e:
        print(f"Error en API Dashboard: {e}")
        return jsonify({'error': str(e)}), 500


# ==========================
# HISTORIAL COMPLETO
# ==========================
@dashboard_bp.route('/history')
@login_required
def history():
    # Vista con todos los movimientos del usuario.
    all_transactions = Transaction.query.filter_by(user_id=current_user.id)\
                                        .order_by(desc(Transaction.timestamp))\
                                        .all()
    return render_template('Dashboard/history.html', transactions=all_transactions)
