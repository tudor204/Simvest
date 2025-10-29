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


from app.controllers.MarketController import market_bp
app.register_blueprint(market_bp)
from app.controllers.DashboardController import dashboard_bp
app.register_blueprint(dashboard_bp)



from app.controllers import (
    IndexController,
    RegisterController,
    LoginController
    
   
)