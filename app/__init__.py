from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from .config import Config
from app.utils.historical_storage import load_historical_storage, preload_favorites
import threading

# =========================================================
# 0. Cargar variables de entorno
# =========================================================
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
app = Flask(__name__)
app.config.from_object(Config)  # Cargar configuración primero

# Inicializar las extensiones con la app
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

# =========================================================
# 3. Cargar datos históricos y precargar activos
# =========================================================
load_historical_storage()  # Carga el JSON existente en memoria
threading.Thread(target=preload_favorites, daemon=True).start()  # Precarga en segundo plano

# =========================================================
# 4. Importar Modelos y Controladores
# =========================================================
from .models import User  # Si se necesita aquí para login_manager

from app.controllers.MarketController import market_bp
app.register_blueprint(market_bp)

from app.controllers.DashboardController import dashboard_bp
app.register_blueprint(dashboard_bp)

from app.controllers import (
    IndexController,
    RegisterController,
    LoginController
)
