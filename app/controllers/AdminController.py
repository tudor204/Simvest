from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import app
from app.models import db, User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/admin/users')
@login_required
def admin_users():
    """Panel de administración de usuarios (solo para admins)"""
    if current_user.role != 'admin':
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('Admin/users.html', users=users)

@admin_bp.route('/admin/user/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """Activar/desactivar usuario"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    action = "activada" if user.is_active else "desactivada"
    flash(f'Cuenta {action} correctamente.', 'success')
    return redirect(url_for('admin_users'))