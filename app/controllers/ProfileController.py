from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db # No importes 'app' aquí para evitar ciclos
from app.models import User

# Definimos el Blueprint
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.route('/', methods=['GET'])
@login_required
def profile():
    """Página de perfil del usuario"""
    
    # 1. Calcular Total Invertido (Sumar cantidad * precio de cada holding)
    total_invested = 0
    # Asegúrate de que tu modelo User tiene la relación 'holdings'
    if hasattr(current_user, 'holdings'):
        for holding in current_user.holdings:
            total_invested += (holding.quantity * holding.purchase_price)
            
    # 2. Contar Transacciones
    transactions_count = 0
    # Asegúrate de que tu modelo User tiene la relación 'transactions'
    if hasattr(current_user, 'transactions'):
        transactions_count = len(current_user.transactions)

    # 3. Enviamos las variables a la plantilla
    return render_template('Profile/profile.html', 
                           user=current_user,
                           total_invested=total_invested,
                           transactions_count=transactions_count)

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Editar perfil de usuario"""
    if request.method == 'POST':
        try:
            # Actualizar datos básicos
            current_user.first_name = request.form.get('first_name', current_user.first_name)
            current_user.last_name = request.form.get('last_name', current_user.last_name)
            current_user.bio = request.form.get('bio', current_user.bio)
            current_user.language = request.form.get('language', current_user.language)
            current_user.timezone = request.form.get('timezone', current_user.timezone)
            
            # Verificaciones de Email/Username (Unique constraints)
            new_email = request.form.get('email')
            if new_email and new_email != current_user.email:
                if User.query.filter_by(email=new_email).first():
                    flash('El email ya está en uso.', 'error')
                    return redirect(url_for('profile.edit_profile'))
                current_user.email = new_email
            
            new_username = request.form.get('username')
            if new_username and new_username != current_user.username:
                if User.query.filter_by(username=new_username).first():
                    flash('El usuario ya existe.', 'error')
                    return redirect(url_for('profile.edit_profile'))
                current_user.username = new_username
            
            db.session.commit()
            flash('Perfil actualizado correctamente.', 'success')
            return redirect(url_for('profile.profile')) # Nota el prefijo 'profile.'
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el perfil.', 'error')
            print(f"Error: {e}") # Usa print o current_app.logger
    
    return render_template('Profile/edit_profile.html', user=current_user)

@profile_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Cambiar contraseña"""
    current_pw = request.form.get('current_password')
    new_pw = request.form.get('new_password')
    confirm_pw = request.form.get('confirm_password')
    
    if not current_user.check_password(current_pw):
        flash('La contraseña actual es incorrecta.', 'error')
        return redirect(url_for('profile.edit_profile'))
    
    if new_pw != confirm_pw:
        flash('Las nuevas contraseñas no coinciden.', 'error')
        return redirect(url_for('profile.edit_profile'))
    
    current_user.set_password(new_pw)
    db.session.commit()
    
    flash('Contraseña actualizada. Inicia sesión de nuevo.', 'success')
    return redirect(url_for('profile.profile'))

# -------------------------------------------------------
# ⚡ RUTA API PARA EL AJAX DEL FRONTEND (CORREGIDA)
# -------------------------------------------------------
@profile_bp.route('/api/stats') 
@login_required
def user_stats():
    """API JSON para las tarjetas de estadísticas"""
    
    # 1. Calcular Total Invertido
    # Asumiendo que tienes una relación 'holdings' o 'transactions'
    # Ajusta esta lógica según tu modelo real de Holding
    total_invested = 0.0
    if hasattr(current_user, 'holdings'):
        for holding in current_user.holdings:
            # Ejemplo: cantidad * precio_promedio
            total_invested += (holding.quantity * holding.avg_price)
            
    # 2. Contar transacciones
    transactions_count = len(current_user.transactions) if hasattr(current_user, 'transactions') else 0

    return jsonify({
        'total_invested': total_invested,  # ¡Es vital para el JS!
        'transactions_count': transactions_count,
        'capital': current_user.capital
    })