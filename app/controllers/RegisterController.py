from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user
from app import app
from app.models import db, bcrypt, User # Importar extensiones y modelo

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Si el usuario ya está logueado, redirige a la página principal
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Obtener datos del formulario
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # 1. Verificar si el usuario o email ya existe
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('El nombre de usuario o el correo electrónico ya está en uso.', 'error')
            return redirect(url_for('register'))

        # 2. Hashear la contraseña de forma segura
        # La función generate_password_hash usa bcrypt por defecto
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # 3. Crear y guardar el nuevo usuario
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        # 4. Loguear al usuario automáticamente
        login_user(user)
        flash(f'¡Cuenta creada con éxito para {username}!', 'success')
        return redirect(url_for('home'))

    return render_template('Register/register.html')
