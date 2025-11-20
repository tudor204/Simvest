import yfinance as yf
import pandas as pd
import time
from app.utils.utils import MARKET_UNIVERSE
from datetime import datetime, timedelta

# =========================================================
# CACHÉ DE DATOS EN VIVO
# =========================================================
market_cache = {"list": [], "dict": {}, "timestamp": 0}
CACHE_DURATION = 600    # segundos = 10 min

def safe_get(info, keys, default=None):
    """Obtiene valor de forma segura probando múltiples keys"""
    for key in keys:
        if key in info and info[key] is not None:
            return info[key]
    return default

def get_asset_price_and_change(ticker, symbol):
    """Obtiene precio y cambio de forma robusta para cualquier tipo de activo"""
    try:
        info = ticker.info
        hist_data = ticker.history(period="2d", interval="1d")
        
        # Múltiples formas de obtener el precio actual
        current_price = safe_get(info, ['currentPrice', 'regularMarketPrice', 'navPrice'])
        
        # Si no hay precio en info, usar historical data
        if not current_price and not hist_data.empty:
            current_price = hist_data['Close'].iloc[-1]
        
        # Múltiples formas de obtener previous close
        previous_close = safe_get(info, ['previousClose', 'regularMarketPreviousClose'])
        if not previous_close and len(hist_data) > 1:
            previous_close = hist_data['Close'].iloc[-2]
        elif not previous_close:
            previous_close = current_price
            
        # Calcular cambio porcentual
        if current_price and previous_close and previous_close > 0:
            change_pct = ((current_price - previous_close) / previous_close * 100)
            change_str = f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"
        else:
            change_str = "0.00%"
            
        return current_price or 0.0, change_str, hist_data
        
    except Exception as e:
        print(f"Error obteniendo precio para {symbol}: {e}")
        return 0.0, "0.00%", None

# =========================================================
# FUNCIÓN NUEVA: Obtener detalles de un solo activo (Rápida)
# =========================================================
def fetch_single_asset_details(symbol):
    """
    Obtiene el precio actual y el nombre de un único activo, optimizado para transacciones.
    Reutiliza la lógica robusta de yfinance.
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # Obtenemos precio y cambio con la función ya existente (pero el historial se ignora)
        price, _, _ = get_asset_price_and_change(ticker, symbol)
        
        # Obtenemos el nombre para la transacción
        info = ticker.info
        name = safe_get(info, ['longName', 'shortName'])
        
        if price > 0:
            return {'price': price, 'name': name}
        return None
    except Exception as e:
        print(f"❌ Error al obtener detalles para {symbol}: {e}")
        return None

# =========================================================
# FUNCIÓN: Obtener datos en vivo de todo el mercado (Con caché)
# =========================================================
def fetch_live_market_data():
    """Obtiene datos en vivo de todos los activos con caché."""
    global market_cache
    now = time.time()
    if now - market_cache["timestamp"] < CACHE_DURATION:
        return market_cache["list"], market_cache["dict"]
    products_list, products_dict = [], {}    
    
    # Procesar activos en lotes más chicos para evitar timeouts
    batch_size = 20
    for i in range(0, len(MARKET_UNIVERSE), batch_size):
        batch = MARKET_UNIVERSE[i:i + batch_size]        
        try:
            # Descargar datos del batch actual
            symbols = [a['symbol'] for a in batch]
            ticker_data = yf.Tickers(' '.join(symbols))
            
            for asset in batch:
                symbol = asset['symbol']
                try:
                    ticker = ticker_data.tickers[symbol]
                    
                    # Obtener precio y cambio
                    price, change_str, hist_data = get_asset_price_and_change(ticker, symbol)
                    
                    # Obtener mini histórico
                    history = []
                    if hist_data is not None and not hist_data.empty:
                        history = hist_data['Close'].tail(10).tolist()
                    else:
                        history = [price] if price else [0.0]
                    
                    # Construir producto con campos adaptados
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
                    fallback = {
                        "name": asset["name"],
                        "symbol": symbol, 
                        "category": asset["category"],
                        "price": 0.0, 
                        "change": "Error", 
                        "history": [0.0]
                    }
                    products_list.append(fallback)
                    products_dict[symbol] = fallback
                    
        except Exception as e:
            print(f"❌ Error en batch {i}: {e}")
            # Agregar fallbacks para todo el batch
            for asset in batch:
                fallback = {
                    "name": asset["name"],
                    "symbol": asset["symbol"],
                    "category": asset["category"],
                    "price": 0.0,
                    "change": "Error",
                    "history": [0.0]
                }
                products_list.append(fallback)
                products_dict[asset['symbol']] = fallback

    market_cache = {"list": products_list, "dict": products_dict, "timestamp": now}
    print(f"✅ Datos cargados: {len(products_list)} activos")
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
    important_periods = ['1D', '1S', '1M', '6M']
    for asset in MARKET_UNIVERSE:
        for period in important_periods:
            fetch_historical_data(asset['symbol'], period)


def get_simple_chart_data(current_total_value, days=7):
    """Genera datos para el gráfico (simplificado para rendimiento)"""
    labels = []
    values = []
    # Aquí simulamos una leve variación para que el gráfico no sea plano si no tienes histórico real guardado
    import random
    for i in range(days):
        date = datetime.now() - timedelta(days=days-1-i)
        labels.append(date.strftime("%Y-%m-%d"))
        # Pequeña variación aleatoria para efecto visual si no hay datos históricos reales
        variation = random.uniform(0.98, 1.02) 
        if i == days - 1: variation = 1 # El último día es el valor real
        values.append(current_total_value * variation)
    
    return {"labels": labels, "values": values}


def get_asset_details(symbol, category):
    """Obtiene detalles específicos del activo según su categoría usando yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Campos base comunes
        asset_details = {
            'name': info.get('longName', info.get('shortName', 'N/A')),
            'symbol': symbol,
            'category': category,
            'description': info.get('longBusinessSummary', 'Sin descripción disponible.'),
            'current_price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
            'previous_close': info.get('previousClose', 0)
        }
        
        # Campos específicos por categoría
        if category == 'fondos':
            asset_details.update({
                'sector': 'Fondo de Inversión',
                'industry': info.get('category', 'N/A'),
                'market_cap': info.get('totalAssets', 'N/A'),
                'expense_ratio': info.get('annualReportExpenseRatio', 'N/A'),
                'ytd_return': info.get('ytdReturn', 'N/A'),
                'total_assets': info.get('totalAssets', 'N/A')
            })
        else:
            # Para acciones, ETFs, crypto, etc.
            asset_details.update({
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A')
            })
        
        return asset_details
        
    except Exception as e:
        print(f"Error obteniendo detalles para {symbol}: {e}")
        return None