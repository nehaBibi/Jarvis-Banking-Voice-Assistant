from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import time

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')
logger = logging.getLogger(__name__)

@chat_bp.route('', methods=['POST'])
def chat():
    from app.utils.decorators import require_auth
    from app.services.chatbot import ChatbotService
    from app.utils.security import SecurityValidator
    
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return error_response(401, 'AUTH_REQUIRED', 'Missing authorization'), 401
    
    token = auth_header.split(' ', 1)[1]
    
    from app.services.auth import AuthService
    user_info = AuthService.verify_token(token)
    if not user_info:
        return error_response(401, 'INVALID_TOKEN', 'Token invalid or expired'), 401
    
    user_id = user_info['user_id']
    
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id', 'default')
    
    is_valid, error = SecurityValidator.validate_message(user_message)
    if not is_valid:
        return error_response(400, 'INVALID_MESSAGE', error), 400
    
    user_message = SecurityValidator.sanitize_message(user_message)
    
    try:
        start_time = time.time()
        
        response = ChatbotService.process_message(
            query=user_message,
            user_id=user_id,
            session_id=session_id
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Chat response: user={user_id}, agent={response.get('agent')}, latency={latency_ms:.0f}ms")
        
        return jsonify({
            'success': True,
            'data': {
                'reply': response.get('reply'),
                'agent': response.get('agent'),
                'query_type': response.get('query_type'),
                'intent': response.get('intent'),
                'safe': response.get('safe', True)
            },
            'meta': {
                'latency_ms': round(latency_ms, 2),
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return error_response(500, 'INTERNAL_ERROR', 'Chat processing failed'), 500

@chat_bp.route('/history', methods=['GET'])
def chat_history():
    from app.services.auth import AuthService
    
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return error_response(401, 'AUTH_REQUIRED', 'Missing authorization'), 401
    
    token = auth_header.split(' ', 1)[1]
    user_info = AuthService.verify_token(token)
    if not user_info:
        return error_response(401, 'INVALID_TOKEN', 'Token invalid or expired'), 401
    
    user_id = user_info['user_id']
    limit = request.args.get('limit', 50, type=int)
    
    try:
        from app.utils.database import get_chat_history
        history = get_chat_history(user_id, limit)
        
        return jsonify({
            'success': True,
            'data': {
                'history': history,
                'count': len(history)
            },
            'meta': {
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
    
    except Exception as e:
        logger.error(f"History fetch error: {str(e)}")
        return error_response(500, 'INTERNAL_ERROR', 'Failed to fetch history'), 500

@chat_bp.route('/history', methods=['DELETE'])
def clear_history():
    from app.services.auth import AuthService
    
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return error_response(401, 'AUTH_REQUIRED', 'Missing authorization'), 401
    
    token = auth_header.split(' ', 1)[1]
    user_info = AuthService.verify_token(token)
    if not user_info:
        return error_response(401, 'INVALID_TOKEN', 'Token invalid or expired'), 401
    
    user_id = user_info['user_id']
    
    try:
        from app.utils.database import clear_user_chat_history
        clear_user_chat_history(user_id)
        
        return jsonify({
            'success': True,
            'data': {'message': 'Chat history cleared'},
            'meta': {'timestamp': datetime.utcnow().isoformat()}
        }), 200
    
    except Exception as e:
        logger.error(f"Clear history error: {str(e)}")
        return error_response(500, 'INTERNAL_ERROR', 'Failed to clear history'), 500

def error_response(status_code, error_code, message):
    return {
        'success': False,
        'error': {
            'code': error_code,
            'message': message
        },
        'meta': {
            'timestamp': datetime.utcnow().isoformat(),
            'status': status_code
        }
    }
