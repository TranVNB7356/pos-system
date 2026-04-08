import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            # Dùng SQLite, file sẽ được lưu trong thư mục /tmp trên Render
            # Hoặc dùng đường dẫn tương đối
            db_path = os.environ.get('DATABASE_PATH', 'pos.db')
            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row
            print(f"✅ Kết nối SQLite thành công! DB: {db_path}")
            self.create_tables()
        except Exception as e:
            print(f"❌ Lỗi kết nối database: {e}")

    def create_tables(self):
        cursor = self.connection.cursor()
        
        # Bảng sản phẩm
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(15,0) NOT NULL,
                cost_price DECIMAL(15,0) DEFAULT 0,
                stock INTEGER DEFAULT 0,
                category VARCHAR(100),
                barcode VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Bảng khách hàng
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(20),
                email VARCHAR(255),
                address TEXT,
                total_spent DECIMAL(15,0) DEFAULT 0,
                last_purchase TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Bảng đơn hàng
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number VARCHAR(50) UNIQUE NOT NULL,
                customer_id INTEGER REFERENCES customers(id),
                total_amount DECIMAL(15,0) NOT NULL,
                payment_method VARCHAR(50) DEFAULT 'cash',
                status VARCHAR(50) DEFAULT 'completed',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Bảng chi tiết đơn hàng
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER REFERENCES orders(id),
                product_id INTEGER REFERENCES products(id),
                quantity INTEGER NOT NULL,
                price DECIMAL(15,0) NOT NULL
            )
        """)
        
        self.connection.commit()
        
        # Thêm dữ liệu mẫu
        self.insert_sample_data()
        cursor.close()

    def insert_sample_data(self):
        cursor = self.connection.cursor()
        
        # Thêm sản phẩm mẫu
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            sample_products = [
                ('Cà phê đen', 15000, 8000, 100, 'Đồ uống', 'SP001'),
                ('Cà phê sữa', 20000, 10000, 100, 'Đồ uống', 'SP002'),
                ('Bánh mì thịt', 25000, 15000, 50, 'Đồ ăn', 'SP003'),
                ('Trà đào', 30000, 18000, 80, 'Đồ uống', 'SP004'),
                ('Nước ép cam', 35000, 20000, 60, 'Đồ uống', 'SP005'),
            ]
            for p in sample_products:
                cursor.execute("""
                    INSERT INTO products (name, price, cost_price, stock, category, barcode)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, p)
        
        # Thêm khách hàng mẫu
        cursor.execute("SELECT COUNT(*) FROM customers")
        if cursor.fetchone()[0] == 0:
            sample_customers = [
                ('Nguyễn Văn A', '0987654321', 'a@gmail.com', 'Hà Nội'),
                ('Trần Thị B', '0978123456', 'b@gmail.com', 'TP HCM'),
                ('Lê Văn C', '0965111222', 'c@gmail.com', 'Đà Nẵng'),
            ]
            for c in sample_customers:
                cursor.execute("""
                    INSERT INTO customers (name, phone, email, address)
                    VALUES (?, ?, ?, ?)
                """, c)
        
        self.connection.commit()
        cursor.close()

    def execute_query(self, query, params=None):
        cursor = self.connection.cursor()
        try:
            # Chuyển đổi %s thành ? cho SQLite
            query = query.replace('%s', '?')
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Lỗi query: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    def fetch_all(self, query, params=None):
        cursor = self.connection.cursor()
        try:
            query = query.replace('%s', '?')
            cursor.execute(query, params or ())
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
            query = query.replace('%s', '?')
            cursor.execute(query, params or ())
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
