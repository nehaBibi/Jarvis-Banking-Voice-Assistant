from flask import Blueprint, jsonify
from datetime import datetime
import time

health_bp = Blueprint('health', __name__, url_prefix='')

startup_time = time.time()

@health_bp.route('/health', methods=['GET'])
def health():
    uptime_seconds = int(time.time() - startup_time)
    return jsonify({
        'success': True,
        'data': {
            'status': 'ok',
            'uptime_seconds': uptime_seconds
        },
        'meta': {
            'timestamp': datetime.utcnow().isoformat()
        }
    }), 200

@health_bp.route('/ready', methods=['GET'])
def readiness():
    from app.utils.database import verify_db_connection
    
    db_ok = verify_db_connection()
    
    if db_ok:
        return jsonify({
            'success': True,
            'data': {
                'ready': True,
                'database': 'connected'
            },
            'meta': {
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
    else:
        return jsonify({
            'success': False,
            'data': {
                'ready': False,
                'database': 'disconnected'
            },
            'meta': {
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 503

@health_bp.route('/live', methods=['GET'])
def liveness():
    return jsonify({
        'success': True,
        'data': {
            'live': True
        },
        'meta': {
            'timestamp': datetime.utcnow().isoformat()
        }
    }), 200
