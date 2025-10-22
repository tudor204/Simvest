from flask import render_template, redirect, url_for, flash
from flask_login import login_required, logout_user, current_user
from app import app

# Ruta principal de la aplicación
@app.route('/')
def index():
    # Si el usuario ya está autenticado (logueado), lo redirigimos directamente a su dashboard (/home)
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    # Si no está autenticado, mostramos la landing page (Index/index.html)
    return render_template('Index/index.html')

# Ruta del Dashboard (Página protegida)
@app.route('/home')
@login_required # Esta protección asegura que si NO está logueado, será enviado a /login
def home():
    # Aquí puedes pasar cualquier dato que necesites mostrar en el dashboard
    return render_template('Home/home.html', username=current_user.username)

# Ruta para cerrar sesión
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    # Redirigimos al usuario a la página de inicio (que ahora redirigirá a /index ya que no estará logueado)
    return redirect(url_for('index'))
