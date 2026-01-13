from flask_login import UserMixin 
from . import db, bcrypt, login_manager 
from datetime import datetime
from sqlalchemy import func # Importamos func para usar current_timestamp

# --- Configuración de Flask-Login ---
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'

@login_manager.user_loader
def load_user(user_id):
    """Función requerida por Flask-Login para cargar un usuario."""
    return db.session.get(User, int(user_id))

# --- Modelos de Base de Datos ---

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    # ID y datos básicos de autenticación
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # Cambiado de password a password_hash
    
    # Datos personales (nuevos campos)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    
    # Sistema de trading
    capital = db.Column(db.Float, nullable=False, default=10000.00)
    
    # Metadatos y control (nuevos campos)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Preferencias (nuevos campos)
    profile_picture = db.Column(db.String(255))
    bio = db.Column(db.Text)
    language = db.Column(db.String(10), default='es')
    timezone = db.Column(db.String(50), default='UTC')
    
    # Roles y permisos
    role = db.Column(db.String(20), default='user')

    # Métodos de seguridad para contraseñas
    def set_password(self, password):
        """Genera un hash seguro de la contraseña usando bcrypt"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verifica si la contraseña coincide con el hash almacenado usando bcrypt"""
        return bcrypt.check_password_hash(self.password_hash, password)

    # Propiedad para compatibilidad (si algún código usa user.password)
    @property
    def password(self):
        raise AttributeError('La contraseña no es un atributo legible')

    @password.setter
    def password(self, password):
        self.set_password(password)

    def get_full_name(self):
        """Devuelve el nombre completo del usuario"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Holding(db.Model):    
    __tablename__ = 'holdings'
    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)    
    symbol = db.Column(db.String(10), nullable=False) 
    name = db.Column(db.String(100), nullable=False)     
    quantity = db.Column(db.Float, nullable=False)    
    purchase_price = db.Column(db.Float, nullable=False) 
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)    
    user = db.relationship('User', backref=db.backref('holdings', lazy=True))

    def __repr__(self):
        return f"Holding('{self.symbol}', UserID: {self.user_id}, Quantity: {self.quantity})"


class Transaction(db.Model):
    """
    Representa un registro HISTÓRICO e INMUTABLE de una compra o venta.
    Esencial para el historial del usuario y el cálculo de P&L.
    
    Todos los campos relacionados con la ejecución (precio, comisión, etc.)
    son snapshots en el momento de la transacción → determinista y auditable.
    """
    __tablename__ = 'transactions'

    # ID y Claves
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Datos de la Operación
    symbol = db.Column(db.String(10), nullable=False)
    asset_name = db.Column(db.String(255))  # Snapshot del nombre del activo
    
    # Tipo: 'BUY' o 'SELL'
    type = db.Column(db.String(10), nullable=False) 
    
    # Valores Transaccionados
    quantity = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)  # Precio ejecutado (snapshot)
    total_amount = db.Column(db.Float, nullable=False)  # quantity * price_per_unit (ANTES de comisión)
    
    # Comisiones y costos
    commission_amount = db.Column(db.Float, default=0.0)  # Total comisión pagada
    
    # Timestamp y estado
    timestamp = db.Column(db.DateTime, index=True, default=func.current_timestamp())
    status = db.Column(db.String(20), default='executed')  # 'executed', 'pending', 'cancelled'

    # Relación
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))

    def __repr__(self):
        return f"<Transaction {self.type} {self.quantity} {self.symbol} @ ${self.price_per_unit} (comm: ${self.commission_amount})>"
    
    @property
    def total_cost(self) -> float:
        """Costo total incluyendo comisión (BUY) o ingreso neto tras comisión (SELL)"""
        if self.type == 'BUY':
            return self.total_amount + self.commission_amount
        else:  # SELL
            return self.total_amount - self.commission_amount


class SimulationConfig(db.Model):
    """
    Configuración global del simulador.
    Define las reglas explícitas: capital inicial, comisiones, límites de operación.
    """
    __tablename__ = 'simulation_config'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Reglas de capital
    initial_capital = db.Column(db.Float, nullable=False, default=10000.00)
    
    # Comisiones (como porcentaje, ej: 0.0005 = 0.05%)
    commission_rate = db.Column(db.Float, nullable=False, default=0.0005)
    
    # Límites de operación
    min_trade_amount = db.Column(db.Float, nullable=False, default=1.0)
    max_position_size_pct = db.Column(db.Float, default=0.25)  # 25% del portfolio
    
    # Metadatos
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SimulationConfig initial_capital=${self.initial_capital} commission={self.commission_rate*100}%>"