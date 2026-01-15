from flask import Blueprint, render_template
from flask_login import login_required

# Crear blueprint para Training
training_bp = Blueprint('training', __name__, url_prefix='/training')

@training_bp.route('/', methods=['GET'])
@login_required
def training():
    """
    Muestra la página de formación con términos de inversión,
    preguntas frecuentes y diferencias entre métodos de inversión.
    """
    return render_template('Training/training.html')
