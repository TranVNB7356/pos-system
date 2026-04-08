from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import Database
from datetime import datetime
import hashlib
import os  # Thêm dòng này nếu chưa có

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-it'

db = Database()

# ==================== TRANG WEB (BỎ LOGIN) ====================

@app.route('/')
def index():
    """Trang chủ - không cần login"""
    return render_template('index.html')

@app.route('/products')
def products_page():
    """Trang quản lý sản phẩm - không cần login"""
    return render_template('products.html')

@app.route('/orders')
def orders_page():
    """Trang quản lý đơn hàng - không cần login"""
    return render_template('orders.html')

# ==================== API ENDPOINTS (BỎ SESSION) ====================

@app.route('/api/current-user')
def current_user():
    """Trả về user mặc định (không cần login)"""
    return jsonify({
        'username': 'Admin',
        'role': 'admin'
    })

@app.route('/api/stats')
def get_stats():
    """Lấy thống kê cho dashboard"""
    total_products = db.fetch_one("SELECT COUNT(*) as count FROM products")
    total_orders = db.fetch_one("SELECT COUNT(*) as count FROM orders")
    today_revenue = db.fetch_one("""
        SELECT COALESCE(SUM(total_amount), 0) as total 
        FROM orders 
        WHERE DATE(created_at) = CURDATE()
    """)
    total_users = db.fetch_one("SELECT COUNT(*) as count FROM users")
    
    return jsonify({
        'total_products': total_products['count'] if total_products else 0,
        'total_orders': total_orders['count'] if total_orders else 0,
        'today_revenue': float(today_revenue['total']) if today_revenue else 0,
        'total_users': total_users['count'] if total_users else 0
    })

@app.route('/api/products', methods=['GET'])
def get_products():
    """Lấy danh sách sản phẩm"""
    products = db.fetch_all("""
        SELECT p.*, c.name as category_name 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.id DESC
    """)
    return jsonify(products)

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Lấy chi tiết 1 sản phẩm"""
    product = db.fetch_one("SELECT * FROM products WHERE id = %s", (product_id,))
    if product:
        return jsonify(product)
    return jsonify({'error': 'Product not found'}), 404

@app.route('/api/products', methods=['POST'])
def add_product():
    """Thêm sản phẩm mới"""
    data = request.json
    query = """
        INSERT INTO products (name, price, stock, category_id, barcode)
        VALUES (%s, %s, %s, %s, %s)
    """
    product_id = db.execute_query(query, (
        data['name'],
        data['price'],
        data.get('stock', 0),
        data.get('category_id'),
        data.get('barcode')
    ))
    
    if product_id:
        return jsonify({'success': True, 'id': product_id})
    return jsonify({'success': False, 'message': 'Không thể thêm sản phẩm'})

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Cập nhật sản phẩm"""
    data = request.json
    query = """
        UPDATE products 
        SET name=%s, price=%s, stock=%s, category_id=%s, barcode=%s
        WHERE id=%s
    """
    result = db.execute_query(query, (
        data['name'],
        data['price'],
        data.get('stock', 0),
        data.get('category_id'),
        data.get('barcode'),
        product_id
    ))
    
    if result is not None:
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Xóa sản phẩm"""
    result = db.execute_query("DELETE FROM products WHERE id=%s", (product_id,))
    if result is not None:
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Lấy danh sách đơn hàng"""
    orders = db.fetch_all("""
        SELECT o.*, u.username as created_by_name
        FROM orders o
        LEFT JOIN users u ON o.created_by = u.id
        ORDER BY o.created_at DESC
        LIMIT 100
    """)
    return jsonify(orders)

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order_detail(order_id):
    """Lấy chi tiết đơn hàng"""
    order = db.fetch_one("SELECT * FROM orders WHERE id = %s", (order_id,))
    items = db.fetch_all("""
        SELECT oi.*, p.name as product_name
        FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = %s
    """, (order_id,))
    
    return jsonify({'order': order, 'items': items})

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Tạo đơn hàng mới"""
    data = request.json
    items = data.get('items', [])
    
    if not items:
        return jsonify({'success': False, 'message': 'Giỏ hàng trống'})
    
    # Tạo mã đơn hàng
    order_number = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Tính tổng tiền
    total = sum(item['price'] * item['quantity'] for item in items)
    
    # Tạo đơn hàng (created_by mặc định là 1 - admin)
    order_query = """
        INSERT INTO orders (order_number, total_amount, payment_method, created_by)
        VALUES (%s, %s, %s, %s)
    """
    order_id = db.execute_query(order_query, (
        order_number,
        total,
        data.get('payment_method', 'cash'),
        1  # user_id mặc định = 1 (admin)
    ))
    
    if not order_id:
        return jsonify({'success': False, 'message': 'Không thể tạo đơn hàng'})
    
    # Thêm chi tiết đơn hàng và cập nhật tồn kho
    for item in items:
        item_query = """
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s)
        """
        db.execute_query(item_query, (order_id, item['id'], item['quantity'], item['price']))
        
        # Cập nhật tồn kho
        update_stock_query = "UPDATE products SET stock = stock - %s WHERE id = %s"
        db.execute_query(update_stock_query, (item['quantity'], item['id']))
    
    return jsonify({
        'success': True,
        'order_id': order_id,
        'order_number': order_number,
        'total': total
    })

# ==================== XÓA BỎ CÁC API LOGIN/LOGOUT ====================
# (không cần nữa)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)