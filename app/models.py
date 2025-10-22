from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_bcrypt import Bcrypt
from flask import Flask

# Inicializar extensiones globalmente
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

# Configurar la vista de login y el mensaje
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False) # Contraseña hasheada

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

@login_manager.user_loader
def load_user(user_id):
    """Función requerida por Flask-Login para cargar un usuario."""
    return User.query.get(int(user_id))
