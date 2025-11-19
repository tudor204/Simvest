from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user
from app import app
from app.models import db, User  # Importar extensiones y modelo

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name', '')  # Nuevo campo, opcional
        last_name = request.form.get('last_name', '')    # Nuevo campo, opcional

        # 1. Verificar si el usuario o email ya existe
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('El nombre de usuario o el correo electrónico ya está en uso.', 'error')
            return redirect(url_for('register'))

        # 2. Crear el nuevo usuario con los nuevos campos
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)  # Esto establece el password_hash

        db.session.add(user)
        db.session.commit()
        
        # 3. Loguear al usuario automáticamente
        login_user(user)
        flash(f'¡Cuenta creada con éxito para {username}!', 'success')
        return redirect(url_for('dashboard.dashboard'))

    return render_template('Register/register.html')