from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
import sqlite3
import stripe
import stripe.error
import smtplib
from email.mime.text import MIMEText
from database import (
    initialize_database,
    add_to_cart, 
    remove_from_cart, 
    get_cart_count,
    get_merchandise, 
    get_cart_items, 
    get_samples_presets,
    create_user,
    authenticate_user,
    get_DUBs,
    create_order,
    add_order_item,
    create_payment
)
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'sk_test_51PaxFWRtUc623uMcmGrmY0XCLDtbNrRH3MJ9qvHtwK0ZT3bUWA1a6XZwyllBiMxODn1vc3qM6RJf5TxAfopOgxn000AFbVIT3R'

initialize_database()

stripe.api_key = 'sk_test_51PaxFWRtUc623uMcmGrmY0XCLDtbNrRH3MJ9qvHtwK0ZT3bUWA1a6XZwyllBiMxODn1vc3qM6RJf5TxAfopOgxn000AFbVIT3R'

@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        email = request.form.get('email')
        total_price = sum(item['price'] * item['quantity'] for item in get_cart_items())
        status = 'pending'

        # Retrieve the customer_id from the database or generate a new one
        customer_id = get_customer_id(email)
        if not customer_id:
            customer_id = create_customer(email)

        order_id = create_order(customer_id, total_price, status, email)
        create_payment(order_id, payment_method='card', payment_status='pending', amount=total_price)
        send_email(email, order_id)

        # Clear the cart
        cart_items = get_cart_items()
        for item in cart_items:
            remove_from_cart(item['id'])

        print(f"Creating order for customer {customer_id}, email {email}, total price {total_price}, status {status}")
        return redirect(url_for('success'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_customer_id(email):
    with sqlite3.connect('database.db', timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM Customers WHERE email =?', (email,))
        customer_id = cursor.fetchone()
        return customer_id[0] if customer_id else None

def create_customer(email):
    with sqlite3.connect('database.db', timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Customers (email) VALUES (?)', (email,))
        conn.commit()
        return cursor.lastrowid

def send_email(to_email, order_id):
    subject = "Your order confirmation"
    body = f"Thank you for your order! Your order id is {order_id}."
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'your_email@example.com'
    msg['To'] = to_email

    try:
        with smtplib.SMTP('smtp.example.com', 587) as server:
            server.starttls()
            server.login('your_email@example.com', 'your_password')
            server.sendmail('your_email@example.com', to_email, msg.as_string())
        print(f"Email sent to {to_email}")
    except smtplib.SMTPException as e:
        print(f"Error sending email: {e}")

@app.route('/process_payment', methods=['POST'])
def process_payment():
    cart_items = get_cart_items()
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)

    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(total_price * 100),
            currency='czk',
            description='PRDK merchandise purchase',
            payment_method_types=['card'],
            metadata={'integration_check': 'accept_a_payment'}
        )
        return jsonify({'clientSecret': payment_intent.client_secret}), 200
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 403

@app.route('/success', methods=['GET'])
def success():
    return render_template('success.html')

@app.route('/')
def index():
    merchandise = get_merchandise()
    samples_presets = get_samples_presets()
    return render_template('index.html', merchandise=merchandise, samples_presets=samples_presets)

@app.route('/other')
def other():
    DUBs = get_DUBs()
    return render_template('other.html', DUBs=DUBs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        create_user(username, password, email)
        flash('Registrace úspěšná! Nyní se můžete přihlásit.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/get_cart_count', methods=['GET'])
def get_cart_count_route():
    try:
        count = get_cart_count()
        return jsonify({'count': count})
    except sqlite3.OperationalError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = authenticate_user(username)
        if user and user[2] == request.form['Password']:
            session['user_id'] = user['UserID']
            flash('Přihlášení úspěšné!')
            return redirect(url_for('index'))
        flash('Neplatné uživatelské jméno nebo heslo.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Odhlášení úspěšné!')
    return redirect(url_for('index'))

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart_route():
    item_id = request.form.get('itemId')
    if item_id:
        try:
            with sqlite3.connect('database.db', timeout=10) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT quantity FROM DUBs WHERE id = ?', (item_id,))
                dub = cursor.fetchone()
                
                if dub:
                    if dub[0] > 0:
                        add_to_cart(item_id)
                        cursor.execute('UPDATE DUBs SET quantity = quantity - 1 WHERE id = ?', (item_id,))
                        conn.commit()
                        return jsonify({'success': True}), 200
                    else:
                        return jsonify({'error': 'Nedostatečné množství na skladě'}), 400
                else:
                    cursor.execute('SELECT quantity FROM Items WHERE id = ?', (item_id,))
                    item = cursor.fetchone()
                    
                    if item and item[0] > 0:
                        add_to_cart(item_id)
                        cursor.execute('UPDATE Items SET quantity = quantity - 1 WHERE id = ?', (item_id,))
                        conn.commit()
                        return jsonify({'success': True}), 200
                    else:
                        return jsonify({'error': 'Nedostatečné množství na skladě'}), 400
                        
        except sqlite3.OperationalError as e:
            print(f"OperationalError: {e}")
            return jsonify({'error': str(e)}), 500
        except Exception as e:
            print(f"Exception: {e}")
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Neplatný požadavek'}), 400

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart_route():
    item_id = request.form.get('itemId')
    if item_id:
        try:
            with sqlite3.connect('database.db', timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT quantity FROM CartItems WHERE item_id = ?', (item_id,))
                cart_item = cursor.fetchone()
                if cart_item:
                    cursor.execute('UPDATE DUBs SET quantity = quantity + ? WHERE id = ?', (cart_item[0], item_id))
                    cursor.execute('DELETE FROM CartItems WHERE item_id = ?', (item_id,))
                    conn.commit()
                    return jsonify({'success': True}), 200
                else:
                    return jsonify({'error': 'Položka nenalezena v košíku'}), 400
        except sqlite3.OperationalError as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Neplatný požadavek'}), 400

@app.route('/cart')
def cart():
    cart_items = get_cart_items()
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/update_quantity', methods=['POST'])
def update_quantity_route():
    data = request.get_json()
    item_id = data.get('itemId')
    quantity = data.get('quantity')

    if item_id and quantity is not None:
        try:
            with sqlite3.connect('database.db', timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE CartItems
                SET quantity = ?
                WHERE id = ?
                ''', (quantity, item_id))
                conn.commit()
                return jsonify({'success': True}), 200
        except sqlite3.OperationalError as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Neplatný požadavek'}), 400


# print(f"Creating order for customer {get_customer_id}, email {email}, total price {total_price}, status {status}")


if __name__ == '__main__':
    app.run(debug=True)
