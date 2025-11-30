from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user, login_required
from app import app
from app.models import db, User
from datetime import datetime

# Blueprint para todo lo relacionado con autenticación (login, logout, gestión básica de cuenta).
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/logout')
@login_required
def logout():
    # Cierro la sesión del usuario actual y lo mando al login.
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('login'))

@auth_bp.route('/account/delete', methods=['POST'])
@login_required
def delete_account():
    # Antes de eliminar la cuenta pido la contraseña para asegurar que es el dueño real.
    password = request.form.get('password')
    
    if not current_user.check_password(password):
        flash('Contraseña incorrecta. No se pudo eliminar la cuenta.', 'error')
        return redirect(url_for('profile'))
    
    try:
        # Hago borrado lógico: el usuario queda inactivo pero no se pierde su historial.
        current_user.is_active = False
        
        # Reasigno email y username para evitar conflictos si se registra otra persona igual.
        current_user.email = f"deleted_{current_user.id}_{current_user.email}"
        current_user.username = f"deleted_{current_user.id}"
        
        db.session.commit()
        
        # Después de marcarlo como eliminado, cierro sesión.
        logout_user()
        flash('Tu cuenta ha sido eliminada correctamente.', 'success')
        return redirect(url_for('login'))
        
    except Exception as e:
        # Si algo falla, deshago todo para no dejar datos corruptos.
        db.session.rollback()
        flash('Error al eliminar la cuenta.', 'error')
        app.logger.error(f'Error deleting account: {e}')
        return redirect(url_for('profile'))
