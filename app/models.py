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
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)   
    capital = db.Column(db.Float, nullable=False, default=10000.00) 

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
    """
    __tablename__ = 'transactions'

    # ID y Claves
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Datos de la Operación
    symbol = db.Column(db.String(10), nullable=False)
    
    # Tipo: 'BUY' o 'SELL'
    type = db.Column(db.String(10), nullable=False) 
    
    # Valores Transaccionados
    quantity = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False) # quantity * price_per_unit
    
    # Timestamp
    timestamp = db.Column(db.DateTime, index=True, default=func.current_timestamp())

    # Relación
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))

    def __repr__(self):
        return f"<Transaction {self.type} {self.quantity} of {self.symbol} at ${self.price_per_unit}>"