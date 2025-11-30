from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user
from app import app
from app.models import db, User  # Importar extensiones y modelo

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Si el usuario ya está autenticado, evitar que vuelva a la página de registro
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        # Obtener datos del formulario
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Nuevos campos opcionales: nombre y apellido
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')

        # 1. Validación: comprobar si ya existe un usuario con ese username o correo
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash('El nombre de usuario o el correo electrónico ya está en uso.', 'error')
            return redirect(url_for('register'))

        # 2. Crear el nuevo usuario incluyendo los campos adicionales
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )

        # Guardar la contraseña en formato hash
        user.set_password(password)

        # Guardar el usuario en la base de datos
        db.session.add(user)
        db.session.commit()
        
        # 3. Iniciar sesión automáticamente después de registrarse
        login_user(user)
        flash(f'¡Cuenta creada con éxito para {username}!', 'success')

        # Redirigir al dashboard inmediatamente
        return redirect(url_for('dashboard.dashboard'))

    # Si es un GET, mostrar el formulario de registro
    return render_template('Register/register.html')
