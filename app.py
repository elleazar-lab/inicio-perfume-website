import psycopg2
import psycopg2.extras
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from db_config import get_db_connection
from datetime import datetime, timedelta


app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_this'

@app.route('/')
def home():
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get product IDs for featured products
    cursor.execute("SELECT id FROM products WHERE name = 'VERY NAUGHTY'")
    very_naughty = cursor.fetchone()
    
    cursor.execute("SELECT id FROM products WHERE name = 'YOU SHOULD'")
    you_should = cursor.fetchone()
    
    cursor.execute("SELECT id FROM products WHERE name = 'BURN FOR YOU'")
    burn_for_you = cursor.fetchone()
    
    cursor.execute("SELECT id FROM products WHERE name = 'DIVINE SIN'")
    divine_sin = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    return render_template('index.html', 
                         very_naughty_id=very_naughty['id'] if very_naughty else 1,
                         you_should_id=you_should['id'] if you_should else 1,
                         burn_for_you_id=burn_for_you['id'] if burn_for_you else 1,
                         divine_sin_id=divine_sin['id'] if divine_sin else 1)

@app.route('/products')
def products():
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM products")
    all_products = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('products.html', products=all_products)

# ========== SHOPPING CART ROUTES ==========

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    quantity = int(request.form['quantity'])
    
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404
    
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    
    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += quantity
    else:
        cart[str(product_id)] = {
            'id': product_id,
            'name': product['name'],
            'price': float(product['price']),
            'quantity': quantity
        }
    
    session['cart'] = cart
    session.modified = True
    
    # Return JSON for AJAX requests
    return jsonify({'success': True})

@app.route('/cart')
def view_cart():
    cart_items = []
    subtotal = 0
    discount = 0
    total = 0
    
    if 'cart' in session:
        for item in session['cart'].values():
            item_subtotal = item['price'] * item['quantity']
            subtotal += item_subtotal
            cart_items.append({
                'id': item['id'],
                'name': item['name'],
                'price': item['price'],
                'quantity': item['quantity'],
                'subtotal': item_subtotal
            })
    
    total_quantity = sum(item['quantity'] for item in cart_items)
    number_of_pairs = total_quantity // 2
    
    if number_of_pairs > 0:
        regular_total = subtotal
        discount = number_of_pairs * 99
        total = regular_total - discount
    else:
        total = subtotal
    
    return render_template('cart.html', 
                         cart_items=cart_items, 
                         subtotal=subtotal,
                         discount=discount,
                         total=total,
                         total_quantity=total_quantity,
                         number_of_pairs=number_of_pairs)

@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    quantity = int(request.form['quantity'])
    
    if 'cart' in session and str(product_id) in session['cart']:
        if quantity <= 0:
            del session['cart'][str(product_id)]
        else:
            session['cart'][str(product_id)]['quantity'] = quantity
        session.modified = True
    
    return redirect(url_for('view_cart'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session and str(product_id) in session['cart']:
        del session['cart'][str(product_id)]
        session.modified = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'cart' not in session or not session['cart']:
        return redirect(url_for('view_cart'))
    
    customer_name = request.form['customer_name']
    customer_email = request.form['customer_email']
    address = request.form['address']
    
    total = 0
    for item in session['cart'].values():
        total += item['price'] * item['quantity']
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("""
        INSERT INTO orders (customer_name, customer_email, total_amount, status)
        VALUES (%s, %s, %s, %s)
    """, (customer_name, customer_email, total, 'pending'))
    
    order_id = cursor.lastrowid
    
    for item in session['cart'].values():
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s)
        """, (order_id, item['id'], item['quantity'], item['price']))
        
        cursor.execute("""
            UPDATE products SET stock = stock - %s WHERE id = %s
        """, (item['quantity'], item['id']))
    
    connection.commit()
    cursor.close()
    connection.close()
    
    session.pop('cart', None)
    
    return f"""
    <html>
    <head><title>Order Confirmed</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>Order Confirmed!</h1>
        <p>Thank you for your order, {customer_name}!</p>
        <p>Order #{order_id} has been placed successfully.</p>
        <p>Total amount: ₱{total:.2f}</p>
        <a href="/products" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background: #060644; color: white; text-decoration: none; border-radius: 5px;">Continue Shopping</a>
    </body>
    </html>
    """

@app.route('/place_order', methods=['POST'])
def place_order():
    # Require user to be logged in
    if not session.get('user_id'):
        flash('Please login or create an account to place an order.', 'warning')
        return redirect(url_for('login'))
    
    if 'cart' not in session or not session['cart']:
        return redirect(url_for('view_cart'))
    
    payment_reference = request.form.get('payment_reference', '')
    payment_method = request.form.get('payment_method', 'GCash')
    
    # Validate reference number based on payment method
    import re
    is_valid = False
    
    if payment_method == 'GCash':
        is_valid = re.match(r'^\d{13}$', payment_reference) is not None
    elif payment_method == 'MariBank':
        is_valid = re.match(r'^\d{12}$', payment_reference) is not None
    elif payment_method == 'GoTyme':
        is_valid = re.match(r'^\d{12}$', payment_reference) is not None
    elif payment_method == 'BDO':
        is_valid = re.match(r'^[A-Za-z0-9-]{10,30}$', payment_reference) is not None
    
    if not is_valid:
        flash(f'Invalid {payment_method} reference number format.', 'error')
        return redirect(url_for('checkout_page'))
    
    # Check for duplicate reference
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE payment_reference = %s", (payment_reference,))
    count = cursor.fetchone()[0]
    if count > 0:
        cursor.close()
        connection.close()
        flash('This reference number has already been used. Please check your transaction.', 'error')
        return redirect(url_for('checkout_page'))
    
    # Get form data
    first_name = request.form.get('first_name', '')
    last_name = request.form.get('last_name', '')
    customer_name = f"{first_name} {last_name}".strip()
    customer_email = request.form.get('customer_email', '')
    phone = request.form.get('phone', '')
    address = request.form.get('address', '')
    city = request.form.get('city', '')
    region = request.form.get('region', '')
    postal_code = request.form.get('postal_code', '')
    order_note = request.form.get('order_note', '')
    
    full_address = f"{address}, {city}, {region} {postal_code}".strip()
    
    # Calculate total
    total = 0
    for item in session['cart'].values():
        total += item['price'] * item['quantity']
    
    # Check stock
    for item in session['cart'].values():
        cursor.execute("SELECT stock FROM products WHERE id = %s", (item['id'],))
        result = cursor.fetchone()
        if result:
            current_stock = result[0]
            if current_stock < item['quantity']:
                cursor.close()
                connection.close()
                return f"Insufficient stock for {item['name']}. Available: {current_stock}", 400
    
    # Generate unique order number: YYYYMMDD-HHMMSS-XXXX
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    random_suffix = ''.join(random.choices(string.digits, k=4))
    order_number = f"{timestamp}-{random_suffix}"
    
    # Insert order
    cursor.execute("""
        INSERT INTO orders (order_number, customer_name, customer_email, total_amount, status, payment_method, payment_reference, shipping_address, phone, order_note)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (order_number, customer_name, customer_email, total, 'pending', payment_method, payment_reference, full_address, phone, order_note))
    
    order_id = cursor.lastrowid
    
    # Insert order items and update stock
    for item_id, item in session['cart'].items():
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s)
        """, (order_id, item['id'], item['quantity'], item['price']))
        
        cursor.execute("UPDATE products SET stock = stock - %s WHERE id = %s", (item['quantity'], item['id']))
    
    connection.commit()
    cursor.close()
    connection.close()
    
    # Clear the cart
    session.pop('cart', None)
    
    return render_template('order_confirmation.html', order_number=order_number, total=total, customer_name=customer_name)

# ========== CHECKOUT & ORDER ROUTES ==========

@app.route('/api/cart')
def api_cart():
    cart_items = []
    subtotal = 0
    total_quantity = 0
    
    if 'cart' in session:
        for item in session['cart'].values():
            item_total = item['price'] * item['quantity']
            subtotal += item_total
            total_quantity += item['quantity']
            cart_items.append({
                'id': item['id'],
                'name': item['name'],
                'price': item['price'],
                'quantity': item['quantity']
            })
    
    pairs = total_quantity // 2
    discount = pairs * 99
    total = subtotal - discount
    
    return jsonify({
        'items': cart_items, 
        'subtotal': subtotal,
        'discount': discount,
        'total': total,
        'total_quantity': total_quantity,
        'pairs': pairs
    })

@app.route('/api/user_info')
def user_info():
    if session.get('user_id'):
        return jsonify({
            'id': session.get('user_id'),
            'name': session.get('user_name', ''),
            'email': session.get('user_email', '')
        })
    return jsonify({'id': None, 'name': '', 'email': ''})

@app.route('/checkout_page')
def checkout_page():
    return render_template('checkout.html')

@app.route('/api/payment_references')
def get_payment_references():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT payment_reference FROM orders WHERE payment_reference IS NOT NULL AND payment_reference != ''")
    references = [row[0] for row in cursor.fetchall()]
    cursor.close()
    connection.close()
    return jsonify(references)

@app.route('/api/check_duplicate_reference', methods=['POST'])
def check_duplicate_reference():
    data = request.get_json()
    reference = data.get('reference')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE payment_reference = %s", (reference,))
    count = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    
    return jsonify({'exists': count > 0})

@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    cursor.close()
    connection.close()
    return render_template('order_confirmation.html', order=order)

# ========== ADMIN ROUTES ==========

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('user_id') or session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    products = cursor.fetchall()
    
    cursor.execute("SELECT id, name, email, role, customer_id, created_at FROM users ORDER BY id")
    users = cursor.fetchall()
    
    # Get ALL orders
    cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cursor.fetchall()
    
    # For each order, fetch its items
    for order in orders:
        cursor.execute("""
            SELECT oi.quantity, oi.price, p.name 
            FROM order_items oi 
            JOIN products p ON oi.product_id = p.id 
            WHERE oi.order_id = %s
        """, (order['id'],))
        order_items_data = cursor.fetchall()
        
        if order_items_data:
            item_strings = [f"{item['quantity']}x {item['name']}" for item in order_items_data]
            order['product_list'] = ', '.join(item_strings)
        else:
            order['product_list'] = 'No items'
    
    cursor.execute("SELECT COUNT(*) as count FROM orders")
    orders_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'completed'")
    completed_count = cursor.fetchone()['count']
    
    # Get month total (PostgreSQL version)
    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0) as total 
        FROM orders 
        WHERE status = 'completed' AND EXTRACT(MONTH FROM order_date) = EXTRACT(MONTH FROM CURRENT_DATE)
    """)
    month_total = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'customer'")
    users_count = cursor.fetchone()['count']
    
    # Get sales data from completed orders (PostgreSQL version)
    sales_data = [0, 0, 0, 0, 0, 0]
    for month in range(1, 7):
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as total 
            FROM orders 
            WHERE status = 'completed' AND EXTRACT(MONTH FROM order_date) = %s AND EXTRACT(YEAR FROM order_date) = EXTRACT(YEAR FROM CURRENT_DATE)
        """, (month,))
        result = cursor.fetchone()
        sales_data[month - 1] = float(result['total'])
    
    cursor.execute("SELECT COUNT(DISTINCT customer_email) as count FROM orders WHERE customer_email IS NOT NULL")
    returning_count = cursor.fetchone()['count']
    
    new_count = max(0, users_count - returning_count)
    inactive_count = max(0, users_count - returning_count)
    
    cursor.close()
    connection.close()
    
    return render_template('admin_dashboard.html', 
                         products=products,
                         users=users,
                         orders=orders,
                         orders_count=orders_count,
                         completed_count=completed_count,
                         month_total=f"{month_total:,.2f}",
                         users_count=users_count,
                         sales_data=sales_data,
                         customer_segments=[new_count, returning_count, inactive_count])

@app.route('/admin/update_stock/<int:product_id>', methods=['POST'])
def update_stock(product_id):
    if not session.get('user_id') or session.get('user_role') != 'admin':
        return jsonify({'success': False}), 401
    
    new_stock = int(request.form['stock'])
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE products SET stock = %s WHERE id = %s", (new_stock, product_id))
    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({'success': True})

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not session.get('user_id') or session.get('user_role') != 'admin':
        return jsonify({'success': False}), 401
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({'success': True})

@app.route('/admin/customers')
def admin_customers():
    if not session.get('user_id') or session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, name, email, role, customer_id, created_at FROM users ORDER BY id")
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('admin_customers.html', users=users)

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    if not session.get('user_id') or session.get('user_role') != 'admin':
        return jsonify({'success': False}), 401
    
    data = request.get_json()
    new_password = data.get('password')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET password = %s WHERE id = %s", (new_password, session['user_id']))
    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({'success': True})

@app.route('/admin/add_product', methods=['POST'])
def add_product():
    if not session.get('user_id') or session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    name = request.form['name']
    description = request.form['description']
    price = request.form['price']
    stock = request.form['stock']
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO products (name, description, price, stock)
        VALUES (%s, %s, %s, %s)
    """, (name, description, price, stock))
    connection.commit()
    cursor.close()
    connection.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/orders')
def admin_orders():
    if not session.get('user_id') or session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return jsonify(orders)

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    if not session.get('user_id') or session.get('user_role') != 'admin':
        return jsonify({'success': False}), 401
    
    data = request.get_json()
    new_status = data.get('status')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE orders SET status = %s, updated_at = NOW() WHERE id = %s", (new_status, order_id))
    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({'success': True})

@app.route('/admin/verify_payment/<int:order_id>', methods=['POST'])
def verify_payment(order_id):
    if not session.get('user_id') or session.get('user_role') != 'admin':
        return jsonify({'success': False}), 401
    
    data = request.get_json()
    reference = data.get('reference')
    
    # Validate 13-digit reference
    if not reference or not reference.isdigit() or len(reference) != 13:
        return jsonify({'success': False, 'error': 'Invalid reference number'}), 400
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE orders SET payment_verified = TRUE, status = 'processing' WHERE id = %s AND payment_reference = %s", (order_id, reference))
    affected = cursor.rowcount
    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({'success': affected > 0})

# ========== API ROUTES ==========

@app.route('/api/products')
def api_products():
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, name, description, price, stock FROM products")
    products = cursor.fetchall()
    cursor.close()
    connection.close()
    
    for product in products:
        name = product['name'].upper()
        men_list = ['LAST CALL', 'LAST VIRGIN', 'CHAMPAGNE BLUE', 'CRAVE CONTROL', 'BURNS SO GOOD', 'CALL ME LATER', 'CALL ME NOW', 'JEALOUS TYPE', 'DIVINE SIN', 'VERY NAUGHTY', 'YOU SHOULD']
        women_list = ['AREA SIXTY-NINE', 'KARAT KISSES', 'LACE ME UP', 'VICIOUS BOMB', 'VICIOUS EXTRACT', 'BREAK THE ICE', 'YOU WOULD HAVE', 'JOYFUL FEAR', 'LAST TOUCH', 'PART-TIME ANGEL', 'BURN FOR YOU']
        
        if name in men_list:
            product['category'] = 'men'
        elif name in women_list:
            product['category'] = 'women'
        else:
            product['category'] = 'unisex'
    
    return jsonify(products)

@app.route('/api/sales_data')
def sales_data():
    import calendar
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("""
        SELECT EXTRACT(DAY FROM order_date) as day, COALESCE(SUM(total_amount), 0) as total
        FROM orders 
        WHERE EXTRACT(YEAR FROM order_date) = %s AND EXTRACT(MONTH FROM order_date) = %s
        GROUP BY EXTRACT(DAY FROM order_date)
        ORDER BY day
    """, (year, month))
    
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    
    days_in_month = calendar.monthrange(year, month)[1]
    
    labels = [str(day) for day in range(1, days_in_month + 1)]
    values = [0] * days_in_month
    
    for result in results:
        values[result['day'] - 1] = float(result['total'])
    
    return jsonify({'labels': labels, 'values': values})

# ========== USER AUTHENTICATION ROUTES ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to profile
    if session.get('user_id'):
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            session['user_email'] = user['email']
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('profile'))
        else:
            return render_template('login.html', error='Invalid email or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (name, email, password, role)
                VALUES (%s, %s, %s, 'customer')
            """, (name, email, password))
            
            # Get the new user's ID
            user_id = cursor.lastrowid
            
            # Generate and update customer ID
            customer_id = f"CUST-{str(user_id).zfill(6)}"
            cursor.execute("UPDATE users SET customer_id = %s WHERE id = %s", (customer_id, user_id))
            
            connection.commit()
            return redirect(url_for('login'))
        except:
            return render_template('register.html', error='Email already exists')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/our-story')
def our_story():
    return render_template('our_story.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/dashboard_redirect')
def dashboard_redirect():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    if session.get('user_role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('profile'))

# ========== FORGOT AND RESET PASSWORD API ROUTES ==========

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            connection.close()
            flash('Email address not found.', 'error')
            return redirect(url_for('forgot_password'))
        
        # Generate 6-digit verification code
        code = ''.join(random.choices(string.digits, k=6))
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
        expires_at = datetime.now() + timedelta(minutes=15)
        
        # Save reset request
        cursor.execute("""
            INSERT INTO password_resets (email, token, code, expires_at)
            VALUES (%s, %s, %s, %s)
        """, (email, token, code, expires_at))
        connection.commit()
        cursor.close()
        connection.close()
        
        # In production, send email here
        # For development, display the code
        flash(f'Your verification code is: {code} (This would be sent to your email)', 'success')
        return render_template('reset_password.html', email=email)
    
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['POST'])
def reset_password():
    email = request.form.get('email')
    code = request.form.get('code')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if new_password != confirm_password:
        flash('Passwords do not match.', 'error')
        return render_template('reset_password.html', email=email)
    
    if len(new_password) < 4:
        flash('Password must be at least 4 characters.', 'error')
        return render_template('reset_password.html', email=email)
    
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("""
        SELECT * FROM password_resets 
        WHERE email = %s AND code = %s AND used = FALSE AND expires_at > NOW()
        ORDER BY id DESC LIMIT 1
    """, (email, code))
    reset = cursor.fetchone()
    
    if not reset:
        cursor.close()
        connection.close()
        flash('Invalid or expired verification code.', 'error')
        return redirect(url_for('forgot_password'))
    
    # Update password
    cursor.execute("UPDATE users SET password = %s WHERE email = %s", (new_password, email))
    
    # Mark reset as used
    cursor.execute("UPDATE password_resets SET used = TRUE WHERE id = %s", (reset['id'],))
    
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Password reset successfully! Please login with your new password.', 'success')
    return redirect(url_for('login'))

# ========== SEARCH API ROUTES ==========

@app.route('/api/search_products')
def search_products():
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, name, description, price, image_url FROM products")
    products = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(products)

@app.route('/perfume/<int:product_id>')
def perfume_detail(product_id):
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if not product:
        return "Product not found", 404
    
    return render_template('perfume_detail.html', product=product)

# ========== PROFILE & ADDRESS ROUTES ==========

@app.route('/profile')
def profile():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("SELECT id, name, email, customer_id, created_at FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    
    cursor.execute("SELECT * FROM orders WHERE customer_email = %s ORDER BY order_date DESC", (session['user_email'],))
    orders = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    member_since = user['created_at'].strftime('%B %Y') if user['created_at'] else '2024'
    
    return render_template('profile.html', user=user, orders=orders, member_since=member_since)

@app.route('/api/addresses')
def get_addresses():
    if not session.get('user_id'):
        return jsonify([])
    
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM addresses WHERE user_id = %s ORDER BY id", (session['user_id'],))
    addresses = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return jsonify(addresses)

@app.route('/api/addresses/<int:address_id>')
def get_address(address_id):
    if not session.get('user_id'):
        return jsonify({}), 401
    
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM addresses WHERE id = %s AND user_id = %s", (address_id, session['user_id']))
    address = cursor.fetchone()
    cursor.close()
    connection.close()
    
    return jsonify(address)

@app.route('/profile/update', methods=['POST'])
def update_profile():
    if not session.get('user_id'):
        return jsonify({'success': False}), 401
    
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET name = %s, email = %s WHERE id = %s", (name, email, session['user_id']))
    connection.commit()
    
    session['user_name'] = name
    session['user_email'] = email
    
    cursor.close()
    connection.close()
    
    return jsonify({'success': True})

@app.route('/profile/address', methods=['POST'])
def save_address():
    if not session.get('user_id'):
        return jsonify({'success': False}), 401
    
    data = request.get_json()
    address_id = data.get('id')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    if address_id:
        cursor.execute("""
            UPDATE addresses SET 
                first_name=%s, last_name=%s, street=%s, apartment=%s, 
                postal_code=%s, city=%s, region=%s, phone=%s
            WHERE id=%s AND user_id=%s
        """, (data.get('first_name'), data.get('last_name'), data.get('street'), data.get('apartment'),
              data.get('postal_code'), data.get('city'), data.get('region'), data.get('phone'), 
              address_id, session['user_id']))
    else:
        cursor.execute("""
            INSERT INTO addresses (user_id, first_name, last_name, street, apartment, postal_code, city, region, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (session['user_id'], data.get('first_name'), data.get('last_name'), data.get('street'), 
              data.get('apartment'), data.get('postal_code'), data.get('city'), data.get('region'), data.get('phone')))
    
    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({'success': True})

@app.route('/profile/address/<int:address_id>', methods=['DELETE'])
def delete_address(address_id):
    if not session.get('user_id'):
        return jsonify({'success': False}), 401
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM addresses WHERE id = %s AND user_id = %s", (address_id, session['user_id']))
    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({'success': True})

@app.route('/profile/change_password', methods=['POST'])
def change_customer_password():
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Verify current password
    cursor.execute("SELECT password FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    
    if not user or user['password'] != current_password:
        cursor.close()
        connection.close()
        return jsonify({'success': False, 'error': 'Current password is incorrect'})
    
    # Update to new password
    cursor.execute("UPDATE users SET password = %s WHERE id = %s", (new_password, session['user_id']))
    connection.commit()
    
    cursor.close()
    connection.close()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
