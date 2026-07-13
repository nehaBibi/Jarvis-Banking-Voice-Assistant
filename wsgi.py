from flask import Flask, jsonify
from flask_cors import CORS
import logging
import os
from datetime import datetime
from config import get_config

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))
    
    setup_logging(app)
    logger = logging.getLogger(__name__)
    
    CORS(app, 
        origins=app.config['CORS_ORIGINS'].split(','),
        supports_credentials=True,
        methods=['GET', 'POST', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization', 'X-CSRFToken']
    )
    
    @app.before_request
    def log_request_start():
        import time
        request.start_time = time.time()
        from flask import request
        logger.debug(f"→ {request.method} {request.path} from {request.remote_addr}")
    
    @app.after_request
    def log_request_end(response):
        import time
        from flask import request
        duration_ms = (time.time() - request.start_time) * 1000
        logger.debug(f"← {request.method} {request.path} {response.status_code} ({duration_ms:.0f}ms)")
        
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        
        return response
    
    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.chat import chat_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        return error_response(400, 'BAD_REQUEST', 'Invalid request'), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        return error_response(401, 'AUTH_REQUIRED', 'Authentication required'), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        return error_response(403, 'FORBIDDEN', 'Insufficient permissions'), 403
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return error_response(404, 'NOT_FOUND', 'Resource not found'), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f'Internal error: {str(error)}')
        return error_response(500, 'INTERNAL_ERROR', 'Internal server error'), 500
    
    return app

def error_response(status_code, error_code, message):
    return jsonify({
        'success': False,
        'error': {
            'code': error_code,
            'message': message
        },
        'meta': {
            'timestamp': datetime.utcnow().isoformat(),
            'status': status_code
        }
    })

def setup_logging(app):
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = logging.FileHandler(app.config.get('LOG_FILE', 'logs/app.log'))
    file_handler.setLevel(log_level)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    app.logger.info(f"Starting Jarvis Banking AI on port {port}")
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
