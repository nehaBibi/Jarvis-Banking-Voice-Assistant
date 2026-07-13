import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = 16 * 1024
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'jarvis_ai_banking')
    
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    TESTING = True
    DB_NAME = 'jarvis_ai_testing'
    REDIS_URL = 'redis://localhost:6379/1'
    WTF_CSRF_ENABLED = False

config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def get_config(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    return config_map.get(config_name, DevelopmentConfig)
