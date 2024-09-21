import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Vytvoření tabulky Items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0
    )
    ''')

    # Vytvoření tabulky CartItems
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS CartItems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        FOREIGN KEY (item_id) REFERENCES Items (id)
        UNIQUE(item_id)
    )
    ''')

    # Vytvoření tabulky DUBs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS DUBs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        price REAL,
        quantity INTEGER DEFAULT 0
    )
    ''')

    # Vytvoření tabulky orders
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        email TEXT NOT NULL,
        total_price REAL,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Vytvoření tabulky order_items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price REAL
    )
    ''')

    # Vytvoření tabulky payments
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        payment_method TEXT,
        payment_status TEXT,
        payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        amount REAL
    )
    ''')

    conn.commit()
    conn.close()

def create_order(customer_id, total_price, status, email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO orders (customer_id, email, total_price, status)
    VALUES (?, ?, ?)
    ''', (customer_id, email, total_price, status))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def add_order_item(order_id, product_id, quantity, price):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO order_items (order_id, product_id, quantity, price)
    VALUES (?, ?, ?, ?)
    ''', (order_id, product_id, quantity, price))
    conn.commit()
    conn.close()

def create_payment(order_id, payment_method, payment_status, amount):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO payments (order_id, payment_method, payment_status, amount)
    VALUES (?, ?, ?, ?)
    ''', (order_id, payment_method, payment_status, amount))
    payment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return payment_id

def add_product(title, price, quantity):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO DUBs (title, price, quantity)
    VALUES (?, ?, ?)
    ''', (title, price, quantity))
    conn.commit()
    conn.close()

def get_DUBs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, price, quantity FROM DUBs')
    DUBs = cursor.fetchall()
    return [{'id': dub[0], 'title': dub[1], 'price': dub[2], 'quantity': dub[3]} for dub in DUBs]

def get_merchandise():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, price, quantity FROM Items')
    rows = cursor.fetchall()
    merchandise = [{'id': row[0], 'title': row[1], 'price': row[2], 'quantity': row[3]} for row in rows]
    conn.close()
    return merchandise

def add_to_cart(item_id):
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO CartItems (item_id, quantity)
        VALUES (?, 1)
        ON CONFLICT(item_id) DO UPDATE SET quantity = quantity + 1
        ''', (item_id,))
        conn.commit()

def remove_from_cart(item_id):
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM CartItems WHERE item_id = ?', (item_id,))
        conn.commit()

def get_cart_count():
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM CartItems')
        count = cursor.fetchone()[0]
        return count

def get_cart_items():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT CartItems.item_id, Items.title, Items.price, CartItems.quantity 
    FROM CartItems 
    JOIN Items ON CartItems.item_id = Items.id
    ''')
    rows = cursor.fetchall()
    cart_items = [{'id': row[0], 'title': row[1], 'price': row[2], 'quantity': row[3]} for row in rows]
    conn.close()
    return cart_items

def get_latest_tracks():
    # Dummy implementation for the sake of example
    return []

def get_samples_presets():
    # Dummy implementation for the sake of example
    return []

def create_user(username, password, email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        UserID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username TEXT NOT NULL,
        Password TEXT NOT NULL,
        Email TEXT NOT NULL
    )
    ''')
    cursor.execute('INSERT INTO Users (Username, Password, Email) VALUES (?, ?, ?)', (username, password, email))
    conn.commit()
    conn.close()

def authenticate_user(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Users WHERE Username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_cart_item_quantity(item_id, quantity):
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE CartItems SET quantity = ? WHERE id = ?', (quantity, item_id))
        conn.commit()

# Inicializace databáze a přidání produktů
initialize_database()

# Přidejte své produkty
products = [
]

for product in products:
    add_product(product[0], product[1], product[2])


print('Produkty byly úspěšně přidány do databáze.')
