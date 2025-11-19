from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import app
from app.models import db, User

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@app.route('/profile', methods=['GET'])
@login_required
def profile():
    """Página de perfil del usuario"""
    return render_template('Profile/profile.html', user=current_user)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Editar perfil de usuario"""
    if request.method == 'POST':
        try:
            # Actualizar campos básicos
            current_user.first_name = request.form.get('first_name', current_user.first_name)
            current_user.last_name = request.form.get('last_name', current_user.last_name)
            current_user.bio = request.form.get('bio', current_user.bio)
            
            # Actualizar preferencias
            current_user.language = request.form.get('language', current_user.language)
            current_user.timezone = request.form.get('timezone', current_user.timezone)
            
            # Verificar si el email ya existe (si se cambió)
            new_email = request.form.get('email')
            if new_email and new_email != current_user.email:
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user:
                    flash('El email ya está en uso por otro usuario.', 'error')
                    return redirect(url_for('edit_profile'))
                current_user.email = new_email
            
            # Verificar si el username ya existe (si se cambió)
            new_username = request.form.get('username')
            if new_username and new_username != current_user.username:
                existing_user = User.query.filter_by(username=new_username).first()
                if existing_user:
                    flash('El nombre de usuario ya está en uso.', 'error')
                    return redirect(url_for('edit_profile'))
                current_user.username = new_username
            
            db.session.commit()
            flash('Perfil actualizado correctamente.', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el perfil.', 'error')
            app.logger.error(f'Error updating profile: {e}')
    
    return render_template('Profile/edit_profile.html', user=current_user)

@app.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """Cambiar contraseña del usuario"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.check_password(current_password):
        flash('La contraseña actual es incorrecta.', 'error')
        return redirect(url_for('edit_profile'))
    
    if new_password != confirm_password:
        flash('Las nuevas contraseñas no coinciden.', 'error')
        return redirect(url_for('edit_profile'))
    
    if len(new_password) < 6:
        flash('La contraseña debe tener al menos 6 caracteres.', 'error')
        return redirect(url_for('edit_profile'))
    
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Contraseña cambiada correctamente.', 'success')
    return redirect(url_for('profile'))

@app.route('/profile/upload-avatar', methods=['POST'])
@login_required
def upload_avatar():
    """Subir avatar del usuario (versión básica - URLs)"""
    avatar_url = request.form.get('avatar_url')
    if avatar_url:
        current_user.profile_picture = avatar_url
        db.session.commit()
        flash('Avatar actualizado correctamente.', 'success')
    else:
        flash('URL de avatar no válida.', 'error')
    
    return redirect(url_for('profile'))

@app.route('/api/user/stats')
@login_required
def user_stats():
    """API para obtener estadísticas del usuario"""
    # Ejemplo: contar holdings y transacciones
    holdings_count = len(current_user.holdings)
    transactions_count = len(current_user.transactions)
    
    return jsonify({
        'username': current_user.username,
        'capital': current_user.capital,
        'holdings_count': holdings_count,
        'transactions_count': transactions_count,
        'member_since': current_user.created_at.strftime('%Y-%m-%d') if current_user.created_at else 'N/A'
    })