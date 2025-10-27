import yfinance as yf
from app.utils import MARKET_UNIVERSE
import time
import threading

# --- CACHÉ MEJORADA PARA DATOS HISTÓRICOS ---
historical_cache = {}
asset_details_cache = {}
CACHE_LOCK = threading.Lock()

# Configuración de caché
HISTORICAL_CACHE_DURATION = 3600  # 1 hora para datos históricos
ASSET_DETAILS_CACHE_DURATION = 7200  # 2 horas para detalles de activos
CACHE_DURATION_SECONDS = 600  # 10 minutos para datos de mercado

# --- NUEVAS FUNCIONES PARA CACHÉ HISTÓRICA ---
def get_historical_data(symbol, period):
    """
    Obtiene datos históricos con caché AGGRESIVA
    """
    cache_key = f"historical_{symbol}_{period}"
    current_time = time.time()
    
    with CACHE_LOCK:
        # Verificar caché existente
        if cache_key in historical_cache:
            data, timestamp = historical_cache[cache_key]
            if current_time - timestamp < HISTORICAL_CACHE_DURATION:
                print(f"✅ Cache HIT para {symbol} ({period})")
                return data
        
        print(f"🔄 Cache MISS para {symbol} ({period}), descargando...")
    
    try:
        # Mapeo de periodos optimizado
        period_map = {
            '1D': {'period': '1d', 'interval': '5m', 'limit': 78},
            '1S': {'period': '5d', 'interval': '1h', 'limit': 120},
            '1M': {'period': '1mo', 'interval': '1d', 'limit': 30},
            '6M': {'period': '6mo', 'interval': '1d', 'limit': 126},
            '1A': {'period': '1y', 'interval': '1d', 'limit': 252},
            '5A': {'period': '5y', 'interval': '1wk', 'limit': 260}
        }
        
        if period not in period_map:
            return None
            
        params = period_map[period]
        ticker = yf.Ticker(symbol)
        
        # Descargar datos
        start_time = time.time()
        data = ticker.history(**{k: v for k, v in params.items() if k != 'limit'})
        download_time = time.time() - start_time
        print(f"📥 Descargados datos para {symbol} ({period}) en {download_time:.2f}s")
        
        # Procesar datos
        if not data.empty:
            # Limitar a un número máximo de puntos
            data_subset = data.tail(params.get('limit', 100))
            processed_data = [
                {
                    'time': index.strftime('%Y-%m-%d %H:%M:%S'),
                    'price': float(row['Close'])
                }
                for index, row in data_subset.iterrows()
            ]
            
            # Guardar en caché
            with CACHE_LOCK:
                historical_cache[cache_key] = (processed_data, time.time())
            
            print(f"💾 Datos cacheados para {symbol} ({period}): {len(processed_data)} puntos")
            return processed_data
        else:
            return []
            
    except Exception as e:
        print(f"❌ Error descargando datos históricos para {symbol} ({period}): {e}")
        return None

def preload_historical_data(symbol):
    """
    Precarga los datos históricos más importantes en segundo plano
    """
    print(f"🚀 Precargando datos para {symbol}...")
    
    # Precargar periodos más usados
    important_periods = ['1D', '1S', '1M']
    
    def preload_task():
        for period in important_periods:
            try:
                get_historical_data(symbol, period)
            except Exception as e:
                print(f"⚠️ Error precargando {symbol} ({period}): {e}")
    
    # Ejecutar en segundo plano sin bloquear
    thread = threading.Thread(target=preload_task)
    thread.daemon = True
    thread.start()

def get_asset_details(symbol):
    """
    Función OPTIMIZADA con caché más inteligente
    """
    cache_key = f"detail_{symbol}"
    current_time = time.time()
    
    with CACHE_LOCK:
        if cache_key in asset_details_cache:
            cached_data, timestamp = asset_details_cache[cache_key]
            if current_time - timestamp < ASSET_DETAILS_CACHE_DURATION:
                return cached_data
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Datos esenciales con fallbacks robustos
        current_price = (info.get('currentPrice') or 
                        info.get('regularMarketPrice') or 
                        info.get('ask') or 0)
        
        previous_close = (info.get('previousClose') or 
                         info.get('regularMarketPreviousClose') or 
                         current_price)
        
        asset_data = {
            'name': info.get('longName', info.get('shortName', symbol)),
            'sector': info.get('sector', 'No disponible'),
            'industry': info.get('industry', 'No disponible'),
            'market_cap': info.get('marketCap', 'No disponible'),
            'description': info.get('longBusinessSummary', 'Información no disponible.'),
            'current_price': current_price,
            'previous_close': previous_close,
            'currency': info.get('currency', 'USD'),
        }
        
        # Formatear market cap
        if isinstance(asset_data['market_cap'], (int, float)):
            if asset_data['market_cap'] >= 1e12:
                asset_data['market_cap'] = f"${asset_data['market_cap']/1e12:.2f}T"
            elif asset_data['market_cap'] >= 1e9:
                asset_data['market_cap'] = f"${asset_data['market_cap']/1e9:.2f}B"
            elif asset_data['market_cap'] >= 1e6:
                asset_data['market_cap'] = f"${asset_data['market_cap']/1e6:.2f}M"
        
        with CACHE_LOCK:
            asset_details_cache[cache_key] = (asset_data, time.time())
        
        return asset_data
        
    except Exception as e:
        print(f"❌ Error en get_asset_details para {symbol}: {e}")
        # Datos de fallback mínimos
        fallback_data = {
            'name': symbol,
            'sector': 'No disponible',
            'industry': 'No disponible', 
            'market_cap': 'No disponible',
            'description': 'Error al cargar información.',
            'current_price': 0,
            'previous_close': 0,
            'currency': 'USD'
        }
        
        with CACHE_LOCK:
            asset_details_cache[cache_key] = (fallback_data, time.time())
        
        return fallback_data

# --- CACHÉ PARA DATOS DE MERCADO (EXISTENTE) ---
market_data_cache = {
    "list": [],
    "dict": {},
    "timestamp": 0
}

def fetch_live_market_data():
    """
    Función existente pero con logging mejorado
    """
    global market_data_cache
    current_time = time.time()

    if current_time - market_data_cache["timestamp"] < CACHE_DURATION_SECONDS:
        print("✅ Cache HIT para datos de mercado")
        return market_data_cache["list"], market_data_cache["dict"]

    print("🔄 Cache MISS para datos de mercado, descargando...")
    
    symbols = [p['symbol'] for p in MARKET_UNIVERSE]
    
    try:
        start_time = time.time()
        ticker_data = yf.Tickers(' '.join(symbols))
        history_data = yf.download(symbols, period='7d', interval='1h', progress=False)
        download_time = time.time() - start_time
        print(f"📥 Descargados datos de mercado en {download_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Error de conexión con yfinance: {e}")
        return market_data_cache["list"], market_data_cache["dict"]

    product_list = []
    product_dict = {}

    for p_base in MARKET_UNIVERSE:
        symbol = p_base['symbol']
        
        try:
            data = ticker_data.tickers[symbol]
            price = data.fast_info.get('lastPrice') or data.info.get('regularMarketPrice')
            previous_close = data.fast_info.get('previousClose') or data.info.get('regularMarketPreviousClose')

            if price is None or previous_close is None:
                price = data.history(period="1d", interval="5m")['Close'].iloc[-1] if not data.history(period="1d", interval="5m").empty else 0.0
                previous_close = data.history(period="2d", interval="1d")['Close'].iloc[-2] if not data.history(period="2d", interval="1d").empty else 0.0

            if price == 0 or previous_close == 0:
                change_pct = 0
            else:
                change_pct = ((price - previous_close) / previous_close) * 100
            
            change_str = f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"

            # Historial para sparklines
            history_prices = []
            if symbol in history_data['Close']:
                hist_series = history_data['Close'][symbol]
                history_prices = hist_series.dropna().tail(40).tolist()
            elif len(symbols) == 1:
                history_prices = history_data['Close'].dropna().tail(40).tolist()
            
            if not history_prices:
                history_prices = [price]

            new_product = {
                'name': p_base['name'],
                'symbol': symbol,
                'price': round(price, 4),
                'category': p_base['category'],
                'change': change_str,
                'history': history_prices
            }
            
            product_list.append(new_product)
            product_dict[symbol] = new_product
        
        except Exception as e:
            print(f"❌ Error procesando {symbol}: {e}")
            fallback_product = {
                **p_base,
                'price': 0.00,
                'change': 'Error',
                'history': [0.00]
            }
            product_list.append(fallback_product)
            product_dict[symbol] = fallback_product

    market_data_cache["list"] = product_list
    market_data_cache["dict"] = product_dict
    market_data_cache["timestamp"] = current_time
    
    print(f"💾 Datos de mercado cacheados: {len(product_list)} activos")
    return product_list, product_dict