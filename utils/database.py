"""
Database Configuration and Models for Jarvis Banking AI
Supports both live MySQL and mock fallback for development
"""
import mysql.connector
from mysql.connector import Error
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration settings"""
    HOST = os.getenv('DB_HOST', 'localhost')
    USER = os.getenv('DB_USER', 'root')
    PASSWORD = os.getenv('DB_PASSWORD', '')
    DATABASE = os.getenv('DB_NAME', 'ai_banking_system')
    PORT = int(os.getenv('DB_PORT', 3306))

# Mock data for fallback (when MySQL is not available)
MOCK_PRODUCTS = [
    {
        'product_id': 1,
        'product_name': 'Car Financing',
        'category': 'Auto Financing',
        'min_income': 50000,
        'max_tenure_months': 60,
        'description': 'Fast and flexible car financing options',
        'markup_type': 'Flat Rate'
    },
    {
        'product_id': 2,
        'product_name': 'Home Financing',
        'category': 'Housing Finance',
        'min_income': 150000,
        'max_tenure_months': 360,
        'description': 'Competitive home financing with flexible terms',
        'markup_type': 'Adjustable Rate'
    },
    {
        'product_id': 3,
        'product_name': 'Personal Loan',
        'category': 'Personal Loan',
        'min_income': 25000,
        'max_tenure_months': 60,
        'description': 'Quick personal loans for your needs',
        'markup_type': 'Fixed Rate'
    },
    {
        'product_id': 4,
        'product_name': 'Business Financing',
        'category': 'SME Financing',
        'min_income': 100000,
        'max_tenure_months': 120,
        'description': 'Tailored financing solutions for SMEs',
        'markup_type': 'Fixed Rate'
    },
    {
        'product_id': 5,
        'product_name': 'Education Financing',
        'category': 'Student Finance',
        'min_income': 30000,
        'max_tenure_months': 84,
        'description': 'Affordable financing for educational pursuits',
        'markup_type': 'Fixed Rate'
    },
]

class DatabaseConnection:
    """Singleton database connection manager with fallback to mock data"""
    _instance = None
    _connection = None
    _is_mock = False  # Track if using mock data
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_connection(cls):
        """Get or create database connection (or fallback to mock)"""
        if cls._connection is None or not cls._connection.is_connected():
            try:
                cls._connection = mysql.connector.connect(
                    host=DatabaseConfig.HOST,
                    user=DatabaseConfig.USER,
                    password=DatabaseConfig.PASSWORD,
                    database=DatabaseConfig.DATABASE,
                    port=DatabaseConfig.PORT,
                    autocommit=True
                )
                cls._is_mock = False
                logger.info("✅ Connected to MySQL database")
            except Error as e:
                logger.warning(f"⚠️  MySQL connection failed: {e}")
                logger.info("📋 Using mock database fallback (install MySQL and run: python setup_database.py)")
                cls._is_mock = True
                cls._connection = None
        return cls._connection
    
    @classmethod
    def close_connection(cls):
        """Close database connection"""
        if cls._connection and cls._connection.is_connected():
            cls._connection.close()
            logger.info("Database connection closed")
    
    @classmethod
    def is_using_mock(cls):
        """Check if using mock data"""
        return cls._is_mock

# Query helper functions
def query_financing_products(search_term=None):
    """
    Query financing products from database
    Falls back to mock data if MySQL unavailable
    
    Args:
        search_term: Optional keyword to filter products (category or name)
    
    Returns:
        List of product dictionaries
    """
    try:
        conn = DatabaseConnection.get_connection()
        
        # Use mock data if no connection
        if conn is None:
            logger.debug(f"Using mock product data (search_term: {search_term})")
            if search_term:
                search_lower = search_term.lower()
                return [p for p in MOCK_PRODUCTS 
                        if search_lower in p['product_name'].lower() 
                        or search_lower in p['category'].lower()
                        or search_lower in p['description'].lower()]
            return MOCK_PRODUCTS
        
        # Live database query
        cursor = conn.cursor(dictionary=True)
        
        if search_term:
            query = """
                SELECT product_id, product_name, category, min_income, 
                       max_tenure_months, description, markup_type
                FROM financing_products
                WHERE product_name LIKE %s OR category LIKE %s OR description LIKE %s
            """
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (search_pattern, search_pattern, search_pattern))
        else:
            query = """
                SELECT product_id, product_name, category, min_income, 
                       max_tenure_months, description, markup_type
                FROM financing_products
            """
            cursor.execute(query)
        
        results = cursor.fetchall()
        cursor.close()
        return results
    
    except Exception as e:
        logger.error(f"Error querying financing products: {e}")
        # Fallback to mock data
        if search_term:
            search_lower = search_term.lower()
            return [p for p in MOCK_PRODUCTS 
                    if search_lower in p['product_name'].lower() 
                    or search_lower in p['category'].lower()]
        return MOCK_PRODUCTS

def get_product_by_id(product_id):
    """Get specific financing product by ID"""
    try:
        conn = DatabaseConnection.get_connection()
        
        # Use mock data if no connection
        if conn is None:
            for product in MOCK_PRODUCTS:
                if product['product_id'] == product_id:
                    return product
            return None
        
        # Live database query
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT product_id, product_name, category, min_income, 
                   max_tenure_months, description, markup_type
            FROM financing_products
            WHERE product_id = %s
        """
        cursor.execute(query, (product_id,))
        result = cursor.fetchone()
        cursor.close()
        return result
    
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        # Fallback to mock
        for product in MOCK_PRODUCTS:
            if product['product_id'] == product_id:
                return product
        return None

def log_user_query(user_id, message, intent):
    """Log user query to database"""
    try:
        conn = DatabaseConnection.get_connection()
        
        if conn is None:
            logger.debug(f"Mock log query: user={user_id}, intent={intent}")
            return True
        
        cursor = conn.cursor()
        
        query = """
            INSERT INTO user_queries (user_id, message, intent)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (user_id, message, intent))
        conn.commit()
        cursor.close()
        
        logger.info(f"Logged query for user {user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error logging query: {e}")
        return False

def log_response(query_id, product_id, response_text, confidence):
    """Log agent response to database"""
    try:
        conn = DatabaseConnection.get_connection()
        
        if conn is None:
            logger.debug(f"Mock log response: product_id={product_id}, confidence={confidence}")
            return True
        
        cursor = conn.cursor()
        
        query = """
            INSERT INTO responses (query_id, product_id, response_text, confidence)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (query_id, product_id, response_text, confidence))
        conn.commit()
        cursor.close()
        
        logger.info(f"Logged response for query {query_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error logging response: {e}")
        return False

def get_all_categories():
    """Get all product categories"""
    try:
        conn = DatabaseConnection.get_connection()
        
        # Use mock data if no connection
        if conn is None:
            categories = list(set(p['category'] for p in MOCK_PRODUCTS))
            logger.debug(f"Using mock categories: {categories}")
            return categories
        
        # Live database query
        cursor = conn.cursor()
        
        query = "SELECT DISTINCT category FROM financing_products"
        cursor.execute(query)
        categories = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return categories
    
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        # Fallback to mock
        return list(set(p['category'] for p in MOCK_PRODUCTS))

def search_products_by_category(category):
    """Search products by category"""
    try:
        conn = DatabaseConnection.get_connection()
        
        # Use mock data if no connection
        if conn is None:
            category_lower = category.lower()
            return [p for p in MOCK_PRODUCTS 
                    if category_lower in p['category'].lower()]
        
        # Live database query
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT product_id, product_name, category, min_income, 
                   max_tenure_months, description, markup_type
            FROM financing_products
            WHERE category LIKE %s
        """
        search_pattern = f"%{category}%"
        cursor.execute(query, (search_pattern,))
        results = cursor.fetchall()
        cursor.close()
        return results
    
    except Exception as e:
        logger.error(f"Error searching by category: {e}")
        # Fallback to mock
        category_lower = category.lower()
        return [p for p in MOCK_PRODUCTS 
                if category_lower in p['category'].lower()]

def init_database():
    """Initialize database connection at startup"""
    try:
        conn = DatabaseConnection.get_connection()
        if conn is None:
            logger.warning("📋 Using mock database - install MySQL for full functionality")
            logger.info("   To setup MySQL:")
            logger.info("   1. Install MySQL Server from https://dev.mysql.com/downloads/mysql/")
            logger.info("   2. Run: python setup_database.py")
            return False
        
        if conn.is_connected():
            logger.info("✅ Database initialization successful")
            return True
    except Exception as e:
        logger.error(f"⚠️  Database initialization error: {e}")
        logger.info("📋 System will use mock data fallback")
        return False

