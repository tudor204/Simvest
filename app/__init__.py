from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from .config import Config


# =========================================================
# 0. Cargar variables de entorno
# =========================================================
load_dotenv()

# =========================================================
# 1. Instanciar extensiones
# =========================================================
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

# =========================================================
# 2. Inicializar la app
# =========================================================
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

# =========================================================
# 3. Importar modelos
# =========================================================
from app.models import User  # CORRECTO, evita import circular

# =========================================================
# 4. Registrar blueprints
# =========================================================
from app.controllers.MarketController import market_bp
app.register_blueprint(market_bp)

from app.controllers.DashboardController import dashboard_bp
app.register_blueprint(dashboard_bp)

from app.controllers import IndexController, RegisterController, LoginController
