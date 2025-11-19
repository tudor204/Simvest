from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user, login_required
from app import app
from app.models import db, User
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@app.route('/logout')
@login_required
def logout():
    """Cerrar sesión del usuario"""
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('login'))

@app.route('/account/delete', methods=['POST'])
@login_required
def delete_account():
    """Eliminar cuenta de usuario (borrado lógico)"""
    password = request.form.get('password')
    
    if not current_user.check_password(password):
        flash('Contraseña incorrecta. No se pudo eliminar la cuenta.', 'error')
        return redirect(url_for('profile'))
    
    try:
        # Borrado lógico - marcar como inactivo
        current_user.is_active = False
        current_user.email = f"deleted_{current_user.id}_{current_user.email}"
        current_user.username = f"deleted_{current_user.id}"
        db.session.commit()
        
        logout_user()
        flash('Tu cuenta ha sido eliminada correctamente.', 'success')
        return redirect(url_for('login'))
        
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar la cuenta.', 'error')
        app.logger.error(f'Error deleting account: {e}')
        return redirect(url_for('profile'))