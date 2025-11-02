import yfinance as yf
import time
from app.utils.utils import MARKET_UNIVERSE

# =========================================================
# CACHÉ DE DATOS EN VIVO
# =========================================================
market_cache = {"list": [], "dict": {}, "timestamp": 0}
CACHE_DURATION = 600  # segundos = 10 min

def fetch_live_market_data():
    """Obtiene datos en vivo de todos los activos con caché."""
    global market_cache
    now = time.time()
    if now - market_cache["timestamp"] < CACHE_DURATION:
        return market_cache["list"], market_cache["dict"]

    symbols = [a['symbol'] for a in MARKET_UNIVERSE]
    try:
        ticker_data = yf.Tickers(' '.join(symbols))
        hist_data = yf.download(symbols, period='7d', interval='1h', progress=False)
    except Exception as e:
        print(f"⚠️ Error al descargar datos de mercado: {e}")
        return market_cache["list"], market_cache["dict"]

    products_list, products_dict = [], {}
    for asset in MARKET_UNIVERSE:
        symbol = asset['symbol']
        try:
            data = ticker_data.tickers[symbol]
            info = data.fast_info or {}
            price = info.get('lastPrice') or data.info.get('regularMarketPrice')
            prev_close = info.get('previousClose') or data.info.get('regularMarketPreviousClose')
            if not price or not prev_close:
                hist = data.history(period="2d", interval="1h")
                price = hist['Close'].iloc[-1] if not hist.empty else 0.0
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else price
            change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
            change_str = f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"

            # Mini histórico
            if symbol in hist_data['Close']:
                history = hist_data['Close'][symbol].dropna().tail(40).tolist()
            else:
                history = [price]

            product = {
                "name": asset["name"],
                "symbol": symbol,
                "category": asset["category"],
                "price": round(price, 4),
                "change": change_str,
                "history": history,
            }

            products_list.append(product)
            products_dict[symbol] = product

        except Exception as e:
            print(f"❌ Error procesando {symbol}: {e}")
            fallback = {**asset, "price": 0.0, "change": "Error", "history": [0.0]}
            products_list.append(fallback)
            products_dict[symbol] = fallback

    market_cache = {"list": products_list, "dict": products_dict, "timestamp": now}
    return products_list, products_dict

# =========================================================
# FUNCIÓN: Datos históricos bajo demanda
# =========================================================
def fetch_historical_data(symbol, period):
    """Descarga datos históricos del activo seleccionado bajo demanda."""
    symbol = symbol.upper()
    period = period.upper()
    period_map = {
        '1D': {'period': '1d', 'interval': '5m', 'limit': 78},
        '1S': {'period': '5d', 'interval': '1h', 'limit': 120},
        '1M': {'period': '1mo', 'interval': '1d', 'limit': 30},
        '6M': {'period': '6mo', 'interval': '1d', 'limit': 126},
        '1A': {'period': '1y', 'interval': '1d', 'limit': 252},
        '5A': {'period': '5y', 'interval': '1wk', 'limit': 260},
    }
    if period not in period_map:
        print(f"⚠️ Periodo no válido: {period}")
        return []

    try:
        params = period_map[period]
        ticker = yf.Ticker(symbol)
        data = ticker.history(auto_adjust=True, **{k: v for k, v in params.items() if k != 'limit'})
        if data.empty:
            return []
        subset = data.tail(params.get('limit', 100))
        historical_data = [
            {"time": idx.strftime('%Y-%m-%d %H:%M:%S'), "price": float(row['Close'])}
            for idx, row in subset.iterrows()
        ]
        return historical_data
    except Exception as e:
        print(f"❌ Error al obtener datos históricos de {symbol}: {e}")
        return []

# =========================================================
# FUNCIÓN: Precarga opcional de favoritos
# =========================================================
def preload_favorites():
    """Descarga los datos de los activos principales en segundo plano."""
    from app.utils.utils import MARKET_UNIVERSE
    important_periods = ['1D', '1S', '1M', '6M']
    for asset in MARKET_UNIVERSE:
        for period in important_periods:
            fetch_historical_data(asset['symbol'], period)
