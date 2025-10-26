# app/models.py (VERSIÓN CORREGIDA Y LIMPIA)

from flask_login import UserMixin 
from . import db, bcrypt, login_manager # Importa los objetos ya instanciados desde __init__.py
from datetime import datetime
# Configurar la vista de login y el mensaje (esto es correcto aquí)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    capital = db.Column(db.Float, nullable=False, default=10000.00) 

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

@login_manager.user_loader
def load_user(user_id):
    """Función requerida por Flask-Login para cargar un usuario."""
    return db.session.get(User, int(user_id))



class Holding(db.Model):
    """Representa un activo simulado poseído por un usuario."""
    __tablename__ = 'holdings'
    id = db.Column(db.Integer, primary_key=True)
    
    # Clave Foránea: Vincula esta inversión al usuario
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Datos del activo simulado
    symbol = db.Column(db.String(10), nullable=False) # Ej: 'AAPL', 'GOOGL'
    name = db.Column(db.String(100), nullable=False)  # Ej: 'Apple Inc.'
    
    quantity = db.Column(db.Float, nullable=False)     # Número de acciones compradas
    purchase_price = db.Column(db.Float, nullable=False) # Precio por acción al momento de la compra
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_sold = db.Column(db.Boolean, nullable=False, default=False)
    # Relación bidireccional con User para facilitar consultas
    user = db.relationship('User', backref=db.backref('holdings', lazy=True))

    def __repr__(self):
        return f"Holding('{self.symbol}', UserID: {self.user_id}, Quantity: {self.quantity})"