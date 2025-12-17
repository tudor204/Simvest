from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from .config import Config
from flask_migrate import Migrate
from flask_caching import Cache

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
migrate = Migrate()
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})

# =========================================================
# 2. Inicializar la app
# =========================================================
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt.init_app(app)
cache.init_app(app)

# --- CONFIGURACIÓN LOGIN ---
login_manager.init_app(app)
login_manager.login_view = 'auth.login' # Redirección automática si no está logueado
login_manager.login_message_category = 'error' # Estilo de mensaje flash
# ---------------------------

migrate.init_app(app, db)

# =========================================================
# 3. Importar modelos
# =========================================================
# Importar después de inicializar db para evitar referencias circulares
from app.models import User, Holding, Transaction 

# =========================================================
# 4. Registrar blueprints
# =========================================================
from app.controllers.MarketController import market_bp
app.register_blueprint(market_bp)

from app.controllers.AuthController import auth_bp
app.register_blueprint(auth_bp)

from app.controllers.ProfileController import profile_bp
app.register_blueprint(profile_bp)

from app.controllers.AdminController import admin_bp
app.register_blueprint(admin_bp)

from app.controllers.DashboardController import dashboard_bp
app.register_blueprint(dashboard_bp)


from app.controllers import IndexController, RegisterController, LoginController

# =========================================================
# 5. Registrar Filtros de Plantilla (Jinja2)
# =========================================================
@app.template_filter('currency')
def currency_filter(value):
    """Formatea un valor numérico como una cadena de moneda USD."""
    try:
        val = float(value)
        return f"${val:,.2f}"
    except (ValueError, TypeError, AttributeError):
        return value