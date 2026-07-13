from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    from app.services.auth import AuthService
    from app.utils.security import SecurityValidator
    
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    logger.info(f"Login attempt: {username}")
    
    is_valid, error = SecurityValidator.validate_username(username)
    if not is_valid:
        logger.warning(f"Invalid username: {username}")
        return error_response(400, 'INVALID_USERNAME', error), 400
    
    if not password:
        return error_response(400, 'INVALID_PASSWORD', 'Password required'), 400
    
    try:
        result = AuthService.login(username, password)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': {
                    'access_token': result['token'],
                    'token_type': 'Bearer',
                    'expires_in': result['expires_in'],
                    'user': {
                        'id': username,
                        'name': username.capitalize(),
                        'role': 'customer'
                    }
                },
                'meta': {
                    'timestamp': datetime.utcnow().isoformat()
                }
            }), 200
        else:
            logger.warning(f"Login failed: {result['error']}")
            return error_response(401, 'AUTH_FAILED', result['error']), 401
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return error_response(500, 'INTERNAL_ERROR', 'Login failed'), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    from app.utils.decorators import require_auth
    from app.services.auth import AuthService
    
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return error_response(401, 'AUTH_REQUIRED', 'Missing authorization'), 401
    
    token = auth_header.split(' ', 1)[1]
    
    try:
        AuthService.logout(token)
        return jsonify({
            'success': True,
            'data': {'message': 'Logged out successfully'},
            'meta': {'timestamp': datetime.utcnow().isoformat()}
        }), 200
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return error_response(500, 'INTERNAL_ERROR', 'Logout failed'), 500

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
