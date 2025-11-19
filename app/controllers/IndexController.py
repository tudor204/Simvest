from flask import render_template, redirect, url_for, flash
from flask_login import login_required, logout_user, current_user
from app import app


# Ruta principal de la aplicación
@app.route('/')
def index():
    # Si el usuario ya está autenticado (logueado), lo redirigimos directamente a su dashboard (/home)
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
        
    # Si no está autenticado, mostramos la landing page (Index/index.html)
    return render_template('Index/index.html')

