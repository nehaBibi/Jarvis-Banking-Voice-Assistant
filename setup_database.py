"""
Database initialization script - Import SQL schema and data into MySQL
"""
import mysql.connector
from mysql.connector import Error
import os

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = ''
DB_NAME = 'ai_banking_system'

def import_sql_file(sql_file_path):
    """Import SQL file into MySQL database"""
    try:
        # First, connect without specifying database to create it if needed
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=False
        )
        cursor = conn.cursor()
        
        # Read SQL file
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Execute SQL statements
        # Split by semicolon and execute each statement
        statements = sql_script.split(';')
        
        for statement in statements:
            statement = statement.strip()
            if statement:  # Skip empty statements
                try:
                    cursor.execute(statement)
                    print(f"✅ Executed: {statement[:60]}...")
                except Error as e:
                    print(f"⚠️  Statement error (might be expected): {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Database import completed successfully!")
        return True
    
    except Error as e:
        print(f"❌ Error importing database: {e}")
        return False

if __name__ == '__main__':
    sql_path = r"c:\Users\JOJIS LAPTOPS\Desktop\AI Assistiant\Database\hbl_ai_system.sql"
    
    if not os.path.exists(sql_path):
        print(f"❌ SQL file not found: {sql_path}")
        exit(1)
    
    print(f"Importing database from: {sql_path}")
    import_sql_file(sql_path)
