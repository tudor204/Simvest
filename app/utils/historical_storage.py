import json
import os
import yfinance as yf
from app.utils.utils import MARKET_UNIVERSE 
import threading
import time

# Ruta del archivo donde se guardan los datos
DATA_FILE = os.path.join(os.path.dirname(__file__), "historical_data.json")

# Diccionario global en memoria
historical_storage = {}

# --- Cargar datos desde el archivo al iniciar ---
def load_historical_storage():
    global historical_storage
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                historical_storage = json.load(f)
            print(f"📂 Datos históricos cargados desde {DATA_FILE}")
        except Exception as e:
            print(f"⚠️ Error cargando archivo de datos: {e}")
            historical_storage = {}
    else:
        historical_storage = {}
        print("📁 No existe archivo de datos, se creará uno nuevo cuando se guarden activos.")


def save_historical_storage():
    """Guarda el diccionario completo en el archivo JSON"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(historical_storage, f, indent=2)
        print(f"💾 Datos guardados en {DATA_FILE}")
    except Exception as e:
        print(f"❌ Error guardando datos históricos: {e}")


def get_historical_data(symbol, period):
    """
    Obtiene los datos históricos de un activo.
    Primero busca en memoria (archivo JSON).
    Si no están, los descarga de yfinance y los guarda.
    """
    symbol = symbol.upper()
    period = period.upper()

    # 1️⃣ Buscar si ya tenemos los datos
    if symbol in historical_storage and period in historical_storage[symbol]:
        print(f"✅ Datos encontrados en archivo para {symbol} ({period})")
        return historical_storage[symbol][period]

    # 2️⃣ Si no existen, descargar desde yfinance
    print(f"🔄 Descargando datos históricos desde yfinance para {symbol} ({period})...")
    period_map = {
        '1D': {'period': '1d', 'interval': '5m', 'limit': 78},
        '1S': {'period': '5d', 'interval': '1h', 'limit': 120},
        '1M': {'period': '1mo', 'interval': '1d', 'limit': 30},
        '6M': {'period': '6mo', 'interval': '1d', 'limit': 126},
        '1A': {'period': '1y', 'interval': '1d', 'limit': 252},
        '5A': {'period': '5y', 'interval': '1wk', 'limit': 260}
    }

    if period not in period_map:
        print(f"⚠️ Periodo no válido: {period}")
        return []

    try:
        params = period_map[period]
        ticker = yf.Ticker(symbol)
        data = ticker.history(auto_adjust=True, **{k: v for k, v in params.items() if k != 'limit'})

        if data.empty:
            print(f"⚠️ Sin datos para {symbol}")
            return []

        data_subset = data.tail(params.get('limit', 100))
        processed_data = [
            {
                'time': index.strftime('%Y-%m-%d %H:%M:%S'),
                'price': float(row['Close'])
            }
            for index, row in data_subset.iterrows()
        ]

        # Guardar en el diccionario
        if symbol not in historical_storage:
            historical_storage[symbol] = {}
        historical_storage[symbol][period] = processed_data

        # Guardar en el archivo
        save_historical_storage()

        return processed_data

    except Exception as e:
        print(f"❌ Error descargando datos históricos para {symbol}: {e}")
        return []

def preload_favorites():
    """
    Descarga y guarda automáticamente los datos históricos
    de los activos principales definidos en MARKET_UNIVERSE.
    Se ejecuta en segundo plano al iniciar la app.
    """
    print("🚀 Precargando datos históricos favoritos...")
    start_time = time.time()

    # Definimos los periodos más útiles para precarga
    important_periods = ['1D', '1S', '1M', '6M']

    def preload_task():
        for asset in MARKET_UNIVERSE:
            symbol = asset['symbol']
            for period in important_periods:
                try:
                    data = get_historical_data(symbol, period)
                    if data:
                        print(f"✅ Precargado {symbol} ({period}) con {len(data)} puntos.")
                except Exception as e:
                    print(f"⚠️ Error precargando {symbol} ({period}): {e}")
            time.sleep(0.5)  # ligera pausa para no saturar la API

        total_time = time.time() - start_time
        print(f"📦 Precarga completada en {total_time:.2f}s")

    # Ejecutar en un hilo separado
    thread = threading.Thread(target=preload_task)
    thread.daemon = True
    thread.start()