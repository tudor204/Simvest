import yfinance as yf
from app.utils.utils import MARKET_UNIVERSE
from app.utils.historical_storage import get_historical_data  # Para históricos
import time

# =========================================================
# CACHÉ DE DATOS DE MERCADO
# =========================================================
market_data_cache = {"list": [], "dict": {}, "timestamp": 0}
CACHE_DURATION_SECONDS = 600  # 10 minutos

def fetch_live_market_data():
    """
    Obtiene los datos de mercado en vivo de los activos definidos en MARKET_UNIVERSE.
    Mantiene una caché de 10 minutos para no saturar la API.
    """
    global market_data_cache
    current_time = time.time()

    # Usar caché si está vigente
    if current_time - market_data_cache["timestamp"] < CACHE_DURATION_SECONDS:
        return market_data_cache["list"], market_data_cache["dict"]

    symbols = [p['symbol'] for p in MARKET_UNIVERSE]

    try:
        # Descargar datos en bloque con yfinance
        ticker_data = yf.Tickers(' '.join(symbols))
        history_data = yf.download(symbols, period='7d', interval='1h', progress=False)
    except Exception as e:
        print(f"Error descargando datos de mercado: {e}")
        return market_data_cache["list"], market_data_cache["dict"]

    product_list = []
    product_dict = {}

    for asset in MARKET_UNIVERSE:
        symbol = asset['symbol']
        try:
            data = ticker_data.tickers[symbol]
            price = data.fast_info.get('lastPrice') or data.info.get('regularMarketPrice')
            previous_close = data.fast_info.get('previousClose') or data.info.get('regularMarketPreviousClose')

            # Fallback si no hay datos directos
            if price is None or previous_close is None:
                hist = data.history(period="1d", interval="5m")
                price = hist['Close'].iloc[-1] if not hist.empty else 0.0
                hist_prev = data.history(period="2d", interval="1d")
                previous_close = hist_prev['Close'].iloc[-2] if not hist_prev.empty else 0.0

            change_pct = ((price - previous_close) / previous_close * 100) if previous_close else 0
            change_str = f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"

            # Historial para sparklines
            history_prices = []
            if symbol in history_data['Close']:
                history_prices = history_data['Close'][symbol].dropna().tail(40).tolist()
            elif len(symbols) == 1:
                history_prices = history_data['Close'].dropna().tail(40).tolist()
            if not history_prices:
                history_prices = [price]

            product = {
                'name': asset['name'],
                'symbol': symbol,
                'price': round(price, 4),
                'category': asset['category'],
                'change': change_str,
                'history': history_prices
            }

            product_list.append(product)
            product_dict[symbol] = product

        except Exception as e:
            print(f"Error procesando {symbol}: {e}")
            fallback = {**asset, 'price': 0.0, 'change': 'Error', 'history': [0.0]}
            product_list.append(fallback)
            product_dict[symbol] = fallback

    # Actualizar caché
    market_data_cache["list"] = product_list
    market_data_cache["dict"] = product_dict
    market_data_cache["timestamp"] = current_time

    return product_list, product_dict
