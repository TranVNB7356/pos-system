from flask import Flask, render_template, request, jsonify
from database import Database
import os
from datetime import datetime

app = Flask(__name__)
db = Database()

# ==================== TRANG CHÍNH ====================
@app.route('/')
def index():
    return render_template('index.html')  # Giờ đây là giao diện quản lý

# ==================== DASHBOARD API ====================
@app.route('/api/dashboard/stats')
def dashboard_stats():
    total_products = db.fetch_one("SELECT COUNT(*) as count FROM products")
    total_customers = db.fetch_one("SELECT COUNT(*) as count FROM customers")
    today_revenue = db.fetch_one("SELECT COALESCE(SUM(total_amount), 0) as revenue FROM orders WHERE DATE(created_at) = CURDATE()")
    today_profit = db.fetch_one("""
        SELECT COALESCE(SUM(oi.quantity * (oi.price - p.cost_price)), 0) as profit 
        FROM order_items oi 
        JOIN products p ON oi.product_id = p.id 
        JOIN orders o ON oi.order_id = o.id 
        WHERE DATE(o.created_at) = CURDATE()
    """)
    return jsonify({
        'total_products': total_products['count'] if total_products else 0,
        'total_customers': total_customers['count'] if total_customers else 0,
        'today_revenue': today_revenue['revenue'] if today_revenue else 0,
        'today_profit': today_profit['profit'] if today_profit else 0
    })

@app.route('/api/orders/recent')
def recent_orders():
    orders = db.fetch_all("""
        SELECT o.*, c.name as customer_name 
        FROM orders o 
        LEFT JOIN customers c ON o.customer_id = c.id 
        ORDER BY o.created_at DESC 
        LIMIT 10
    """)
    return jsonify(orders)

# ==================== QUẢN LÝ SẢN PHẨM API ====================
@app.route('/api/products', methods=['GET'])
def get_products():
    products = db.fetch_all("SELECT * FROM products ORDER BY id DESC")
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    product_id = db.execute_query("""
        INSERT INTO products (name, price, cost_price, stock, category, barcode)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (data['name'], data['price'], data.get('cost_price', 0), 
          data.get('stock', 0), data.get('category', ''), data.get('barcode', '')))
    return jsonify({'success': True, 'id': product_id})

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.json
    db.execute_query("""
        UPDATE products 
        SET name=%s, price=%s, cost_price=%s, stock=%s, category=%s, barcode=%s
        WHERE id=%s
    """, (data['name'], data['price'], data.get('cost_price', 0),
          data.get('stock', 0), data.get('category', ''), data.get('barcode', ''), product_id))
    return jsonify({'success': True})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    db.execute_query("DELETE FROM products WHERE id=%s", (product_id,))
    return jsonify({'success': True})

# ==================== QUẢN LÝ KHÁCH HÀNG API ====================
@app.route('/api/customers', methods=['GET'])
def get_customers():
    customers = db.fetch_all("""
        SELECT c.*, 
               COALESCE(SUM(o.total_amount), 0) as total_spent,
               COUNT(o.id) as order_count
        FROM customers c
        LEFT JOIN orders o ON c.id = o.customer_id
        GROUP BY c.id
        ORDER BY c.id DESC
    """)
    return jsonify(customers)

@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.json
    customer_id = db.execute_query("""
        INSERT INTO customers (name, phone, email, address)
        VALUES (%s, %s, %s, %s)
    """, (data['name'], data.get('phone', ''), data.get('email', ''), data.get('address', '')))
    return jsonify({'success': True, 'id': customer_id})

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = request.json
    db.execute_query("""
        UPDATE customers 
        SET name=%s, phone=%s, email=%s, address=%s
        WHERE id=%s
    """, (data['name'], data.get('phone', ''), data.get('email', ''), data.get('address', ''), customer_id))
    return jsonify({'success': True})

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    db.execute_query("DELETE FROM customers WHERE id=%s", (customer_id,))
    return jsonify({'success': True})

@app.route('/api/customers/<int:customer_id>/orders')
def customer_orders(customer_id):
    orders = db.fetch_all("""
        SELECT * FROM orders 
        WHERE customer_id = %s 
        ORDER BY created_at DESC
    """, (customer_id,))
    return jsonify(orders)

# ==================== BÁO CÁO API ====================
@app.route('/api/reports/day')
def report_day():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    revenue = db.fetch_one("SELECT COALESCE(SUM(total_amount), 0) as total FROM orders WHERE DATE(created_at) = %s", (date,))
    cost = db.fetch_one("""
        SELECT COALESCE(SUM(oi.quantity * p.cost_price), 0) as total 
        FROM order_items oi 
        JOIN products p ON oi.product_id = p.id 
        JOIN orders o ON oi.order_id = o.id 
        WHERE DATE(o.created_at) = %s
    """, (date,))
    return jsonify({
        'total_revenue': revenue['total'],
        'total_cost': cost['total'],
        'total_profit': revenue['total'] - cost['total']
    })

@app.route('/api/reports/week')
def report_week():
    # Tuần này
    revenue = db.fetch_one("SELECT COALESCE(SUM(total_amount), 0) as total FROM orders WHERE YEARWEEK(created_at) = YEARWEEK(CURDATE())")
    cost = db.fetch_one("""
        SELECT COALESCE(SUM(oi.quantity * p.cost_price), 0) as total 
        FROM order_items oi 
        JOIN products p ON oi.product_id = p.id 
        JOIN orders o ON oi.order_id = o.id 
        WHERE YEARWEEK(o.created_at) = YEARWEEK(CURDATE())
    """)
    return jsonify({
        'total_revenue': revenue['total'],
        'total_cost': cost['total'],
        'total_profit': revenue['total'] - cost['total']
    })

@app.route('/api/reports/month')
def report_month():
    revenue = db.fetch_one("SELECT COALESCE(SUM(total_amount), 0) as total FROM orders WHERE MONTH(created_at) = MONTH(CURDATE()) AND YEAR(created_at) = YEAR(CURDATE())")
    cost = db.fetch_one("""
        SELECT COALESCE(SUM(oi.quantity * p.cost_price), 0) as total 
        FROM order_items oi 
        JOIN products p ON oi.product_id = p.id 
        JOIN orders o ON oi.order_id = o.id 
        WHERE MONTH(o.created_at) = MONTH(CURDATE()) AND YEAR(o.created_at) = YEAR(CURDATE())
    """)
    return jsonify({
        'total_revenue': revenue['total'],
        'total_cost': cost['total'],
        'total_profit': revenue['total'] - cost['total']
    })

@app.route('/api/reports/year')
def report_year():
    revenue = db.fetch_one("SELECT COALESCE(SUM(total_amount), 0) as total FROM orders WHERE YEAR(created_at) = YEAR(CURDATE())")
    cost = db.fetch_one("""
        SELECT COALESCE(SUM(oi.quantity * p.cost_price), 0) as total 
        FROM order_items oi 
        JOIN products p ON oi.product_id = p.id 
        JOIN orders o ON oi.order_id = o.id 
        WHERE YEAR(o.created_at) = YEAR(CURDATE())
    """)
    return jsonify({
        'total_revenue': revenue['total'],
        'total_cost': cost['total'],
        'total_profit': revenue['total'] - cost['total']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
