from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

dashboard_bp = Blueprint('home', __name__) 

@dashboard_bp.route('/home', methods=['GET'])
@login_required 
def home():
    # El current_user tiene acceso directo al campo 'capital' que acabamos de añadir
    user_capital = current_user.capital

    # Ahora pasamos el capital a la plantilla
    return render_template('Home/home.html', capital=f"{user_capital:,.2f}")
    # Nota: El f-string con :,.2f da formato al número (ej: 10,000.00)