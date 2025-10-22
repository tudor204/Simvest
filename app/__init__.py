import os
from dotenv import load_dotenv
from flask import Flask
from .config import Config # Importar la clase de configuración
from .models import db, login_manager, bcrypt, User # Importar las extensiones

load_dotenv()

# Inicializar la aplicación
app = Flask(__name__)
app.config.from_object(Config) # Cargar la configuración

# Inicializar las extensiones con la aplicación
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)


# Crear las tablas de la base de datos (necesario para SQLite)
with app.app_context():
    db.create_all()

# Importar los controladores al final para evitar errores de importación circular
from app.controllers import (
    IndexController,
    RegisterController,
    LoginController
)