import mysql.connector
from mysql.connector import Error, pooling
import os
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseConfig:
    HOST = os.getenv('DB_HOST', 'localhost')
    USER = os.getenv('DB_USER', 'root')
    PASSWORD = os.getenv('DB_PASSWORD', '')
    DATABASE = os.getenv('DB_NAME', 'ai_banking_system')
    PORT = int(os.getenv('DB_PORT', 3306))

MOCK_PRODUCTS = [
    {'product_id': 1, 'product_name': 'Car Financing', 'category': 'Auto Financing', 'min_income': 50000, 'max_tenure_months': 60},
    {'product_id': 2, 'product_name': 'Home Financing', 'category': 'Housing Finance', 'min_income': 150000, 'max_tenure_months': 360},
    {'product_id': 3, 'product_name': 'Personal Loan', 'category': 'Personal Loan', 'min_income': 25000, 'max_tenure_months': 60},
    {'product_id': 4, 'product_name': 'Business Financing', 'category': 'SME Financing', 'min_income': 100000, 'max_tenure_months': 120},
    {'product_id': 5, 'product_name': 'Education Financing', 'category': 'Student Finance', 'min_income': 30000, 'max_tenure_months': 84},
]

class DatabasePool:
    _instance = None
    _pool = None
    _is_mock = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        try:
            self._pool = pooling.MySQLConnectionPool(
                pool_name='jarvis_pool',
                pool_size=5,
                pool_reset_session=True,
                host=DatabaseConfig.HOST,
                user=DatabaseConfig.USER,
                password=DatabaseConfig.PASSWORD,
                database=DatabaseConfig.DATABASE,
                port=DatabaseConfig.PORT,
                autocommit=True
            )
            self._is_mock = False
            logger.info("✅ Database pool initialized")
        except Error as e:
            logger.warning(f"⚠️  Database pool initialization failed: {e}")
            self._is_mock = True
    
    def get_connection(self):
        if self._pool is None or self._is_mock:
            return None
        
        try:
            return self._pool.get_connection()
        except Error as e:
            logger.warning(f"Failed to get connection: {e}")
            return None
    
    def execute(self, query, params=None, fetch_one=False):
        conn = self.get_connection()
        
        if conn is None:
            logger.debug(f"Using mock data (query: {query[:50]}...)")
            return self._get_mock_data(query, params)
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if 'SELECT' in query.upper():
                if fetch_one:
                    result = cursor.fetchone()
                else:
                    result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.rowcount
            
            cursor.close()
            conn.close()
            return result
        except Error as e:
            logger.error(f"Database error: {e}")
            return None
    
    def _get_mock_data(self, query, params):
        if 'financing_products' in query.lower():
            if params and isinstance(params, tuple):
                search_term = params[0].strip('%').lower()
                return [p for p in MOCK_PRODUCTS if search_term in str(p).lower()]
            return MOCK_PRODUCTS
        return []

_db_pool = None

def get_pool():
    global _db_pool
    if _db_pool is None:
        _db_pool = DatabasePool()
    return _db_pool

def verify_db_connection():
    pool = get_pool()
    if pool._is_mock:
        return False
    
    try:
        conn = pool.get_connection()
        if conn:
            conn.close()
            return True
    except:
        pass
    
    return False

def query_financing_products(search_term=None):
    pool = get_pool()
    
    if search_term:
        query = "SELECT * FROM financing_products WHERE product_name LIKE %s OR category LIKE %s OR description LIKE %s"
        search_pattern = f"%{search_term}%"
        return pool.execute(query, (search_pattern, search_pattern, search_pattern)) or []
    else:
        query = "SELECT * FROM financing_products"
        return pool.execute(query) or []

def get_product_by_id(product_id):
    pool = get_pool()
    query = "SELECT * FROM financing_products WHERE product_id = %s"
    result = pool.execute(query, (product_id,), fetch_one=True)
    return result

def log_chat_interaction(user_id, user_message, agent_name, bot_response, query_type, intent, safe):
    pool = get_pool()
    
    if pool._is_mock:
        logger.debug(f"Mock log: user={user_id}, agent={agent_name}")
        return True
    
    query = """
    INSERT INTO chat_history 
    (user_id, user_message, agent_name, bot_response, query_type, intent, safe, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    try:
        pool.execute(query, (user_id, user_message, agent_name, bot_response, query_type, intent, safe, datetime.utcnow()))
        return True
    except Exception as e:
        logger.error(f"Failed to log interaction: {e}")
        return False

def get_chat_history(user_id, limit=50):
    pool = get_pool()
    
    if pool._is_mock:
        return []
    
    query = "SELECT * FROM chat_history WHERE user_id = %s ORDER BY created_at DESC LIMIT %s"
    
    try:
        result = pool.execute(query, (user_id, limit)) or []
        return result
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        return []

def clear_user_chat_history(user_id):
    pool = get_pool()
    
    if pool._is_mock:
        return True
    
    query = "DELETE FROM chat_history WHERE user_id = %s"
    
    try:
        pool.execute(query, (user_id,))
        return True
    except Exception as e:
        logger.error(f"Failed to clear history: {e}")
        return False

def init_database():
    pool = get_pool()
    return not pool._is_mock
