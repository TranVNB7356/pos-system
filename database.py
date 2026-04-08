import sqlite3
import os

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            # Tạo file database trong thư mục hiện tại
            db_path = os.path.join(os.path.dirname(__file__), 'pos.db')
            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row
            print("✅ Kết nối SQLite thành công!")
            self.create_tables()
        except Exception as e:
            print(f"❌ Lỗi kết nối database: {e}")
    
    def create_tables(self):
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'staff',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                category_id INTEGER,
                barcode TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                total_amount REAL NOT NULL,
                payment_method TEXT DEFAULT 'cash',
                status TEXT DEFAULT 'completed',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL
            )
            """
        ]
        
        for query in queries:
            self.execute_query(query)
        
        # Thêm dữ liệu mẫu
        admin = self.fetch_one("SELECT * FROM users WHERE username = 'admin'")
        if not admin:
            self.execute_query(
                "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                ('admin', 'admin123', 'Administrator', 'admin')
            )
        
        categories = self.fetch_all("SELECT * FROM categories")
        if len(categories) == 0:
            for cat in ['Điện tử', 'Thời trang', 'Thực phẩm']:
                self.execute_query("INSERT INTO categories (name) VALUES (?)", (cat,))
        
        products = self.fetch_all("SELECT * FROM products")
        if len(products) == 0:
            self.execute_query(
                "INSERT INTO products (name, price, stock, category_id) VALUES (?, ?, ?, ?)",
                ('Sản phẩm mẫu 1', 100000, 100, 1)
            )
            self.execute_query(
                "INSERT INTO products (name, price, stock, category_id) VALUES (?, ?, ?, ?)",
                ('Sản phẩm mẫu 2', 200000, 50, 2)
            )
    
    def execute_query(self, query, params=None):
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Lỗi query: {e}")
            return None
        finally:
            cursor.close()
    
    def fetch_all(self, query, params=None):
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Lỗi fetch: {e}")
            return []
        finally:
            cursor.close()
    
    def fetch_one(self, query, params=None):
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            print(f"Lỗi fetch: {e}")
            return None
        finally:
            cursor.close()
    
    def close(self):
        if self.connection:
            self.connection.close()
