import psycopg2
import psycopg2.extras
import os
from urllib.parse import urlparse

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            database_url = os.environ.get('DATABASE_URL')
            if database_url:
                result = urlparse(database_url)
                self.connection = psycopg2.connect(
                    database=result.path[1:],
                    user=result.username,
                    password=result.password,
                    host=result.hostname,
                    port=result.port
                )
                print("✅ Kết nối database PostgreSQL thành công!")
                self.create_tables()
            else:
                raise Exception("DATABASE_URL not found")
        except Exception as e:
            print(f"❌ Lỗi kết nối database: {e}")
    
    def create_tables(self):
        cursor = self.connection.cursor()
        
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'staff',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(10,0) NOT NULL,
                stock INTEGER DEFAULT 0,
                category_id INTEGER,
                barcode VARCHAR(100)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                order_number VARCHAR(50) UNIQUE NOT NULL,
                total_amount DECIMAL(10,0) NOT NULL,
                payment_method VARCHAR(50) DEFAULT 'cash',
                status VARCHAR(50) DEFAULT 'completed',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price DECIMAL(10,0) NOT NULL
            )
            """
        ]
        
        for query in queries:
            cursor.execute(query)
        
        self.connection.commit()
        
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES (%s, %s, %s, %s)",
                ('admin', 'admin123', 'Administrator', 'admin')
            )
        
        cursor.execute("SELECT * FROM categories")
        if len(cursor.fetchall()) == 0:
            categories = ['Điện tử', 'Thời trang', 'Thực phẩm']
            for cat in categories:
                cursor.execute("INSERT INTO categories (name) VALUES (%s)", (cat,))
        
        cursor.execute("SELECT * FROM products")
        if len(cursor.fetchall()) == 0:
            cursor.execute(
                "INSERT INTO products (name, price, stock, category_id) VALUES (%s, %s, %s, %s)",
                ('Sản phẩm mẫu 1', 100000, 100, 1)
            )
            cursor.execute(
                "INSERT INTO products (name, price, stock, category_id) VALUES (%s, %s, %s, %s)",
                ('Sản phẩm mẫu 2', 200000, 50, 2)
            )
        
        self.connection.commit()
        cursor.close()
    
    def execute_query(self, query, params=None):
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor.lastrowid if hasattr(cursor, 'lastrowid') else None
        except Exception as e:
            print(f"Lỗi query: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()
    
    def fetch_all(self, query, params=None):
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Lỗi fetch: {e}")
            return []
        finally:
            cursor.close()
    
    def fetch_one(self, query, params=None):
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
        except Exception as e:
            print(f"Lỗi fetch: {e}")
            return None
        finally:
            cursor.close()
    
    def close(self):
        if self.connection:
            self.connection.close()
