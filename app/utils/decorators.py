from functools import wraps
from flask import request, jsonify
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            logger.warning('Auth: Missing Bearer token')
            return error_response(401, 'AUTH_REQUIRED', 'Missing authorization'), 401
        
        token = auth_header.split(' ', 1)[1]
        
        from app.services.auth import AuthService
        user_info = AuthService.verify_token(token)
        
        if not user_info:
            logger.warning(f'Auth: Invalid token')
            return error_response(401, 'INVALID_TOKEN', 'Token invalid or expired'), 401
        
        kwargs['user_id'] = user_info.get('user_id')
        kwargs['token'] = token
        
        return f(*args, **kwargs)
    
    return decorated_function

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
