from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user
from app import app
from app.models import User  # Importar modelo

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 1. Buscar el usuario por email
        user = User.query.filter_by(email=email).first()
        
        # 2. Verificar si el usuario existe y si la contraseña es correcta usando el método check_password
        if user and user.check_password(password):
            # 3. Iniciar sesión y establecer la cookie 'remember me'
            login_user(user, remember=True)
            
            # 4. Redirigir a la página de destino o a 'home'
            next_page = request.args.get('next')
            flash('Sesión iniciada correctamente.', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.dashboard'))
        else:
            # 5. Mostrar error si las credenciales son inválidas
            flash('Inicio de sesión fallido. Por favor, verifica tu correo y contraseña.', 'error')

    return render_template('Login/login.html')