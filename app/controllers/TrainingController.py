from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.utils.utils import generate_investment_response

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


@training_bp.route('/chat', methods=['POST'])
@login_required
def training_chat():
    """
    Maneja las solicitudes del chat de IA para responder preguntas sobre inversión.
    Ahora retorna sugerencias de preguntas adicionales.
    """
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({
            'success': False,
            'error': 'Mensaje vacío'
        }), 400
    
    # Generar respuesta contextualizada sobre inversión
    ai_response = generate_investment_response(user_message)
    
    return jsonify({
        'success': ai_response.get('success', True),
        'message': user_message,
        'response': ai_response.get('response', ''),
        'suggestions': ai_response.get('suggestions', []),
        'topic': ai_response.get('topic', None)
    })


