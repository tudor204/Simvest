# app/__init__.py (VERSIÓN CORREGIDA)

import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy  # NECESARIO
from flask_login import LoginManager      # NECESARIO
from flask_bcrypt import Bcrypt          # NECESARIO
from .config import Config

load_dotenv()

# =========================================================
# 1. Instanciar/Definir las extensiones globalmente
# =========================================================
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

# =========================================================
# 2. Inicializar la aplicación y configurar extensiones
# =========================================================
# Inicializar la aplicación
app = Flask(__name__)
app.config.from_object(Config) # Cargar la configuración

# Inicializar las extensiones con la aplicación
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

# =========================================================
# 3. Importar Modelos y Controladores (rompiendo el ciclo)
# =========================================================
# *Ahora* es seguro importar el modelo User, ya que db, bcrypt, etc.,
# ya están definidos e inicializados.

from .models import User # Importamos el modelo User (si es necesario aquí, ej: login_manager)

# Crear las tablas de la base de datos (se usa el objeto db ya inicializado)
with app.app_context():
    db.create_all()

def preload_popular_assets():
    """
    Precarga datos de activos populares al iniciar la aplicación
    """
    popular_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META']
    
    def preload_task():
        from app.services.market_api import preload_historical_data
        import time
        
        print("🚀 Precargando datos de activos populares...")
        for symbol in popular_symbols:
            try:
                preload_historical_data(symbol)
                time.sleep(1)  # Espaciar las peticiones
            except Exception as e:
                print(f"⚠️ Error precargando {symbol}: {e}")
    
    # Ejecutar en segundo plano después de que la app esté lista
    import threading
    thread = threading.Thread(target=preload_task)
    thread.daemon = True
    thread.start()


from app.controllers.MarketController import market_bp
app.register_blueprint(market_bp)
from app.controllers.DashboardController import dashboard_bp
app.register_blueprint(dashboard_bp)



from app.controllers import (
    IndexController,
    RegisterController,
    LoginController
    
   
)