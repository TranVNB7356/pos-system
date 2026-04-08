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
            else:
                # Local development - sửa password theo máy bạn
                self.connection = psycopg2.connect(
                    host='localhost',
                    database='pos_db',
                    user='postgres',
                    password='123456'  # Thay bằng mật khẩu PostgreSQL của bạn
                )
            
            print("✅ Kết nối database thành công!")
            self.create_tables()
        except Exception as e:
            print(f"❌ Lỗi kết nối database: {e}")

    def create_tables(self):
        cursor = self.connection.cursor()
        
        # Bảng sản phẩm
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
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
                ('Nước ép cam
