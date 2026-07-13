import hashlib
import uuid
import json
import logging
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class AuthService:
    
    SESSION_STORE = {}
    SESSION_EXPIRY_HOURS = 24
    
    @classmethod
    def _get_session_store(cls):
        if REDIS_AVAILABLE:
            try:
                from config import get_config
                config = get_config()
                redis_url = config.REDIS_URL
                return redis.from_url(redis_url)
            except Exception as e:
                logger.warning(f"Redis not available: {e}. Using in-memory store.")
        
        return None
    
    @classmethod
    def login(cls, username, password):
        if not username or not password:
            return {'success': False, 'error': 'Username and password required'}
        
        session_id = str(uuid.uuid4())
        token = cls._generate_token(username)
        
        expires_at = datetime.utcnow() + timedelta(hours=cls.SESSION_EXPIRY_HOURS)
        expires_in = int(cls.SESSION_EXPIRY_HOURS * 3600)
        
        user_data = {
            'user_id': username,
            'session_id': session_id,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': expires_at.isoformat()
        }
        
        store = cls._get_session_store()
        
        if store:
            try:
                store.setex(
                    f'session:{session_id}',
                    expires_in,
                    json.dumps(user_data)
                )
                logger.info(f"Session created in Redis: {session_id}")
            except Exception as e:
                logger.warning(f"Redis store failed: {e}. Falling back to memory.")
                cls.SESSION_STORE[session_id] = {
                    **user_data,
                    'token': token,
                    'expires_at': expires_at
                }
        else:
            cls.SESSION_STORE[session_id] = {
                **user_data,
                'token': token,
                'expires_at': expires_at
            }
        
        logger.info(f"✅ User authenticated: {username}")
        
        return {
            'success': True,
            'token': token,
            'session_id': session_id,
            'expires_in': expires_in
        }
    
    @classmethod
    def logout(cls, token):
        store = cls._get_session_store()
        
        for session_id, session_data in list(cls.SESSION_STORE.items()):
            if session_data.get('token') == token:
                del cls.SESSION_STORE[session_id]
                logger.info(f"Session invalidated: {session_id}")
        
        if store:
            try:
                pattern = 'session:*'
                for key in store.scan_iter(match=pattern):
                    data = json.loads(store.get(key))
                    if data.get('token') == token:
                        store.delete(key)
            except Exception as e:
                logger.warning(f"Redis logout failed: {e}")
    
    @classmethod
    def verify_token(cls, token):
        store = cls._get_session_store()
        
        if not token:
            return None
        
        for session_id, session_data in cls.SESSION_STORE.items():
            if session_data.get('token') == token:
                if datetime.fromisoformat(session_data['expires_at']) > datetime.utcnow():
                    return {'user_id': session_data['user_id'], 'session_id': session_id}
                else:
                    del cls.SESSION_STORE[session_id]
                    return None
        
        if store:
            try:
                for key in store.scan_iter(match='session:*'):
                    data = json.loads(store.get(key))
                    if data.get('token') == token:
                        return {'user_id': data['user_id']}
            except Exception as e:
                logger.warning(f"Redis verification failed: {e}")
        
        return None
    
    @classmethod
    def _generate_token(cls, user_id):
        payload = f"{user_id}:{uuid.uuid4().hex}"
        return hashlib.sha256(payload.encode()).hexdigest()
