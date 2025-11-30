from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user
from app import app
from app.models import User

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya está logueado, lo mando directo al dashboard para evitar repetir login.
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Busco al usuario por email para validar el inicio de sesión.
        user = User.query.filter_by(email=email).first()
        
        # Si el usuario existe y la contraseña coincide, iniciamos sesión.
        if user and user.check_password(password):
            login_user(user, remember=True)  # Mantengo la sesión activa si cierra el navegador.
            
            # Si venía intentando entrar a una página protegida, lo regreso allí.
            next_page = request.args.get('next')
            flash('Sesión iniciada correctamente.', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.dashboard'))
        
        # Si las credenciales fallan, aviso sin decir cuál dato está mal.
        flash('Inicio de sesión fallido. Verifica tu correo y contraseña.', 'error')

    return render_template('Login/login.html')
