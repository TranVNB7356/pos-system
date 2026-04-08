from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from database import Database
from datetime import datetime, timedelta

app = Flask(__name__)
db = Database()

# ==================== TRANG CHỦ ====================
@app.route('/')
def index():
    return render_template('index.html')

# ==================== QUẢN LÝ SẢN PHẨM ====================
@app.route('/products')
def products_page():
    return render_template('products.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    products = db.fetch_all("SELECT * FROM products ORDER BY id DESC")
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    query = """
        INSERT INTO products (name, price, stock, cost_price, category, barcode)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    product_id = db.execute_query(query, (
        data['name'],
        data['price'],
        data['stock'],
        data.get('cost_price', 0),
        data.get('category', ''),
        data.get('barcode', '')
    ))
    return jsonify({'success': True, 'id': product_id})

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.json
    query = """
        UPDATE products 
        SET name=%s, price=%s, stock=%s, cost_price=%s, category=%s, barcode=%s
        WHERE id=%s
    """
    db.execute_query(query, (
        data['name'],
        data['price'],
        data['stock'],
        data.get('cost_price', 0),
        data.get('category', ''),
        data.get('barcode', ''),
        product_id
    ))
    return jsonify({'success': True})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    db.execute_query("DELETE FROM products WHERE id=%s", (product_id,))
    return jsonify({'success': True})

# ==================== QUẢN LÝ KHÁCH HÀNG ====================
@app.route('/customers')
def customers_page():
    return render_template('customers.html')

@app.route('/api/customers', methods=['GET'])
def get_customers():
    customers = db.fetch_all("SELECT * FROM customers ORDER BY total_spent DESC")
    return jsonify(customers)

@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.json
    query = """
        INSERT INTO customers (name, phone, email, address, total_spent)
        VALUES (%s, %s, %s, %s, %s)
    """
    customer_id = db.execute_query(query, (
        data['name'],
        data.get('phone', ''),
        data.get('email', ''),
        data.get('address', ''),
        0
    ))
    return jsonify({'success': True, 'id': customer_id})

@app.route('/api/customers/<int:customer_id>/history')
def get_customer_history(customer_id):
    orders = db.fetch_all("""
        SELECT o.*, oi.product_id, oi.quantity, oi.price, p.name as product_name
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE o.customer_id = %s
        ORDER BY o.created_at DESC
    """, (customer_id,))
    return jsonify(orders)

# ==================== QUẢN LÝ ĐƠN HÀNG ====================
@app.route('/api/orders', methods=['GET'])
def get_orders():
    orders = db.fetch_all("""
        SELECT o.*, c.name as customer_name 
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
        ORDER BY o.created_at DESC 
        LIMIT 50
    """)
    return jsonify(orders)

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    order_number = f"DH{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Tạo đơn hàng
    query = """
        INSERT INTO orders (order_number, customer_id, total_amount, payment_method, status, created_by)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    order_id = db.execute_query(query, (
        order_number,
        data.get('customer_id'),
        data['total_amount'],
        data.get('payment_method', 'cash'),
        'completed',
        data.get('created_by', 1)
    ))
    
    # Thêm chi tiết đơn hàng và cập nhật tồn kho
    for item in data['items']:
        db.execute_query("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s)
        """, (order_id, item['id'], item['quantity'], item['price']))
        
        # Giảm tồn kho
        db.execute_query("""
            UPDATE products SET stock = stock - %s WHERE id = %s
        """, (item['quantity'], item['id']))
    
    # Cập nhật tổng chi tiêu của khách hàng
    if data.get('customer_id'):
        db.execute_query("""
            UPDATE customers 
            SET total_spent = total_spent + %s,
                last_purchase = NOW()
            WHERE id = %s
        """, (data['total_amount'], data['customer_id']))
    
    return jsonify({'success': True, 'order_id': order_id, 'order_number': order_number})

# ==================== BÁO CÁO THỐNG KÊ ====================
@app.route('/reports')
def reports_page():
    return render_template('reports.html')

@app.route('/api/stats', methods=['GET'])
def get_stats():
    # Tổng quan
    total_products = db.fetch_one("SELECT COUNT(*) as count FROM products")
    total_customers = db.fetch_one("SELECT COUNT(*) as count FROM customers")
    total_orders = db.fetch_one("SELECT COUNT(*) as count FROM orders")
    
    # Doanh thu hôm nay
    today = datetime.now().date()
    today_revenue = db.fetch_one("""
        SELECT COALESCE(SUM(total_amount), 0) as revenue 
        FROM orders 
        WHERE DATE(created_at) = %s
    """, (today,))
    
    # Doanh thu tháng này
    this_month = datetime.now().replace(day=1).date()
    month_revenue = db.fetch_one("""
        SELECT COALESCE(SUM(total_amount), 0) as revenue 
        FROM orders 
        WHERE DATE(created_at) >= %s
    """, (this_month,))
    
    # Lợi nhuận (Doanh thu - Vốn)
    profit_data = db.fetch_one("""
        SELECT 
            COALESCE(SUM(oi.quantity * oi.price), 0) as revenue,
            COALESCE(SUM(oi.quantity * p.cost_price), 0) as cost
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN products p ON oi.product_id = p.id
        WHERE DATE(o.created_at) >= %s
    """, (this_month,))
    
    revenue = profit_data['revenue'] if profit_data else 0
    cost = profit_data['cost'] if profit_data else 0
    profit = revenue - cost
    
    # Top sản phẩm bán chạy
    top_products = db.fetch_all("""
        SELECT p.name, SUM(oi.quantity) as total_sold
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        GROUP BY p.id
        ORDER BY total_sold DESC
        LIMIT 5
    """)
    
    return jsonify({
        'total_products': total_products['count'] if total_products else 0,
        'total_customers': total_customers['count'] if total_customers else 0,
        'total_orders': total_orders['count'] if total_orders else 0,
        'today_revenue': today_revenue['revenue'] if today_revenue else 0,
        'month_revenue': month_revenue['revenue'] if month_revenue else 0,
        'profit': profit,
        'profit_margin': (profit / revenue * 100) if revenue > 0 else 0,
        'top_products': top_products
    })

@app.route('/api/reports/daily')
def daily_report():
    days = int(request.args.get('days', 7))
    reports = db.fetch_all("""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as order_count,
            SUM(total_amount) as revenue
        FROM orders
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """, (days,))
    return jsonify(reports)

@app.route('/api/reports/monthly')
def monthly_report():
    year = int(request.args.get('year', datetime.now().year))
    reports = db.fetch_all("""
        SELECT 
            DATE_FORMAT(created_at, '%%Y-%%m') as month,
            COUNT(*) as order_count,
            SUM(total_amount) as revenue
        FROM orders
        WHERE YEAR(created_at) = %s
        GROUP BY DATE_FORMAT(created_at, '%%Y-%%m')
        ORDER BY month DESC
    """, (year,))
    return jsonify(reports)

# ==================== CHẠY APP ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
