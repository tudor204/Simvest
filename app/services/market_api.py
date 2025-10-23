# app/services/market_api.py

import random
import requests
import json

# NOTA: En una aplicación real, pondrías tu API_KEY en el archivo .env
# ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY') 
# API_URL = 'https://www.alphavantage.co/query'

def get_current_quote(symbol):
    """
    Simulación de la obtención de la cotización actual usando un valor aleatorio.
    En un entorno real, aquí harías la llamada a la API externa.
    """
    # ----------------------------------------------------------------------
    # Lógica de API Real (Ejemplo con Alpha Vantage)
    # ----------------------------------------------------------------------
    # params = {
    #     'function': 'GLOBAL_QUOTE',
    #     'symbol': symbol,
    #     'apikey': ALPHA_VANTAGE_KEY
    # }
    # try:
    #     response = requests.get(API_URL, params=params)
    #     data = response.json()
    #     return float(data['Global Quote']['05. price'])
    # except:
    #     # Retorna un valor simulado si la API falla o estamos simulando
    #     pass
    # ----------------------------------------------------------------------

    # SIMULACIÓN (Usar un precio base y añadir un cambio aleatorio para simular fluctuación)
    
    # Asignamos precios base a los símbolos que ya usamos
    base_prices = {'AAPL': 150.00, 'TSLA': 250.00, 'GOOGL': 1200.00, 'AMZN': 130.00}
    
    if symbol in base_prices:
        base = base_prices[symbol]
        # Aplica una fluctuación aleatoria del +/- 5%
        fluctuation = random.uniform(0.95, 1.05)
        return round(base * fluctuation, 2)
    
    # Si el símbolo no está en la lista simulada, usamos un valor fijo para evitar errores.
    return 100.00

