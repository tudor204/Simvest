from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db  # Importar la DB directamente para evitar ciclos con 'app'
from app.models import User

# ============================================================
# 📌 BLUEPRINT DEL PERFIL DE USUARIO
# ============================================================
# Agrupa todas las rutas relacionadas al perfil bajo /profile
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


# ============================================================
# 📌 PERFIL PRINCIPAL (Vista)
# ============================================================
@profile_bp.route('/', methods=['GET'])
@login_required
def profile():
    """
    Muestra el dashboard del perfil con estadísticas profesionales:
    - Total invertido, ganancia/pérdida, rentabilidad
    - Activos en portafolio, transacciones
    - Distribución de activos y resumen de actividad reciente
    """

    # Inicializar variables
    total_invested = 0
    total_current_value = 0
    active_holdings = 0
    unrealized_gain = 0
    transactions_count = 0
    recent_transactions = []
    holdings_list = []

    if hasattr(current_user, 'holdings') and current_user.holdings:
        for holding in current_user.holdings:
            purchase_cost = holding.quantity * holding.purchase_price
            current_value = holding.quantity * (holding.current_price or holding.purchase_price)
            
            total_invested += purchase_cost
            total_current_value += current_value
            unrealized_gain += (current_value - purchase_cost)
            
            if holding.quantity > 0:
                active_holdings += 1
                holdings_list.append({
                    'name': holding.asset.name,
                    'symbol': holding.asset.symbol,
                    'quantity': holding.quantity,
                    'purchase_price': holding.purchase_price,
                    'current_price': holding.current_price or holding.purchase_price,
                    'percentage': ((current_value - purchase_cost) / purchase_cost * 100) if purchase_cost > 0 else 0
                })

    # Calcular porcentaje de rentabilidad
    roi_percentage = 0
    if total_invested > 0:
        roi_percentage = (unrealized_gain / total_invested) * 100

    # Obtener transacciones recientes (últimas 5)
    if hasattr(current_user, 'transactions') and current_user.transactions:
        transactions_count = len(current_user.transactions)
        recent_transactions = sorted(
            current_user.transactions, 
            key=lambda x: x.created_at, 
            reverse=True
        )[:5]

    # Renderizar plantilla con variables mejoradas
    return render_template(
        'Profile/profile.html',
        user=current_user,
        total_invested=total_invested,
        total_current_value=total_current_value,
        unrealized_gain=unrealized_gain,
        roi_percentage=roi_percentage,
        active_holdings=active_holdings,
        transactions_count=transactions_count,
        recent_transactions=recent_transactions,
        holdings_list=holdings_list
    )


# ============================================================
# 📌 EDITAR PERFIL
# ============================================================
@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Permite al usuario editar su información básica:
    nombre, apellido, biografía, idioma, zona horaria,
    email y nombre de usuario (con validación para evitar duplicados).
    """

    if request.method == 'POST':
        try:
            # Actualizar datos básicos del usuario
            current_user.first_name = request.form.get('first_name', current_user.first_name)
            current_user.last_name = request.form.get('last_name', current_user.last_name)
            current_user.bio = request.form.get('bio', current_user.bio)
            current_user.language = request.form.get('language', current_user.language)
            current_user.timezone = request.form.get('timezone', current_user.timezone)

            # ------------------------------
            # Validación de email único
            # ------------------------------
            new_email = request.form.get('email')
            if new_email and new_email != current_user.email:
                if User.query.filter_by(email=new_email).first():
                    flash('El email ya está en uso.', 'error')
                    return redirect(url_for('profile.edit_profile'))
                current_user.email = new_email

            # ------------------------------
            # Validación de username único
            # ------------------------------
            new_username = request.form.get('username')
            if new_username and new_username != current_user.username:
                if User.query.filter_by(username=new_username).first():
                    flash('El usuario ya existe.', 'error')
                    return redirect(url_for('profile.edit_profile'))
                current_user.username = new_username

            # Confirmar los cambios en BD
            db.session.commit()
            flash('Perfil actualizado correctamente.', 'success')
            return redirect(url_for('profile.profile'))

        except Exception as e:
            # Si algo sale mal revertimos la transacción
            db.session.rollback()
            flash('Error al actualizar el perfil.', 'error')
            print(f"Error: {e}")

    return render_template('Profile/edit_profile.html', user=current_user)


# ============================================================
# 📌 CAMBIAR CONTRASEÑA
# ============================================================
@profile_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """
    Permite al usuario cambiar su contraseña.
    Incluye validaciones de contraseña actual y coincidencia
    entre la nueva contraseña y su confirmación.
    """

    current_pw = request.form.get('current_password')
    new_pw = request.form.get('new_password')
    confirm_pw = request.form.get('confirm_password')

    # 1. Validar contraseña actual
    if not current_user.check_password(current_pw):
        flash('La contraseña actual es incorrecta.', 'error')
        return redirect(url_for('profile.edit_profile'))

    # 2. Validar coincidencia de nuevas contraseñas
    if new_pw != confirm_pw:
        flash('Las nuevas contraseñas no coinciden.', 'error')
        return redirect(url_for('profile.edit_profile'))

    # 3. Guardar la nueva contraseña
    current_user.set_password(new_pw)
    db.session.commit()

    flash('Contraseña actualizada. Inicia sesión de nuevo.', 'success')
    return redirect(url_for('profile.profile'))


# ============================================================
# 📌 API JSON → Estadísticas del usuario (AJAX)
# ============================================================
@profile_bp.route('/api/stats')
@login_required
def user_stats():
    """
    Devuelve estadísticas del usuario en formato JSON.
    Se utiliza en el frontend para actualizar tarjetas y gráficos
    con información en tiempo real.
    """

    # 1. Calcular el total invertido
    # ⚠ Importante: 'avg_price' debe existir en el modelo Holding.
    total_invested = 0.0
    if hasattr(current_user, 'holdings'):
        for holding in current_user.holdings:
            total_invested += (holding.quantity * holding.avg_price)

    # 2. Cantidad de transacciones realizadas
    transactions_count = len(current_user.transactions) if hasattr(current_user, 'transactions') else 0

    # 3. Respuesta JSON para el frontend
    return jsonify({
        'total_invested': total_invested,
        'transactions_count': transactions_count,
        'capital': current_user.capital
    })
