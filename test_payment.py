import os
import sqlite3
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    # Remove the existing database file if it exists
    if os.path.exists('database.db'):
        os.remove('database.db')

    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        phoneNum TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_name VARCHAR(45),
            description VARCHAR(45),
            price DECIMAL(10,2),
            size VARCHAR(10),
            condition VARCHAR(20),
            image_url VARCHAR(255),
            quantity INTEGER,
            created_at DATETIME,
            verified BOOLEAN,
            FOREIGN KEY(user_id) REFERENCES Users(user_id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Shopping_Cart (
        cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users (id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Cart_Items (
        cart_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cart_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (cart_id) REFERENCES Shopping_Cart (cart_id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Orders (
        order_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        order_date DATETIME,
        total_amount DECIMAL(10,2),
        status VARCHAR(20),
        tracking_num VARCHAR(50),
        shipping_address VARCHAR(255),
        created_at DATETIME,
        FOREIGN KEY(user_id) REFERENCES Users(user_id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Order_Items (
         order_item_id INTEGER PRIMARY KEY,
         order_id INTEGER,
         product_id INTEGER,
         quantity INTEGER,
         price DECIMAL(10,2),
         FOREIGN KEY(order_id) REFERENCES Orders(order_id),
         FOREIGN KEY(product_id) REFERENCES Products(product_id)
    )''')
    cursor.execute('''INSERT INTO Users (name, password, phoneNum, email, role)
                  VALUES (?, ?, ?, ?, ?)''', ('testuser', 'password123', '1234567890', 'test@example.com', 'user'))

    cursor.execute('''INSERT INTO Products (user_id, product_name, description, price, size, condition, image_url, quantity, created_at, verified)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (1, 'Test Product', 'Test Description', 10.00, 'Medium', 'New', 'image_url.jpg', 5, '2024-07-01 12:00:00', True))

    cursor.execute('''INSERT INTO Shopping_Cart (user_id)
                  VALUES (?)''', (1,))

    cursor.execute('''INSERT INTO Cart_Items (cart_id, product_id, quantity)
                  VALUES (?, ?, ?)''', (1, 1, 2))
    conn.commit()
    conn.close()

def test_proceed_to_payment(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1  # Simulate a logged-in user

    rv = client.get('/proceed_to_payment', follow_redirects=True)
    assert b'Test Product' in rv.data  
    assert b'Total Amount: 20.00' in rv.data  

def test_process_payment(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1  # Simulate a logged-in user

    rv = client.post('/process_payment', data={
        'shipping_address': '123 Test St',
        'payment_method': 'Credit Card',
        'total_amount': '20.00'
    }, follow_redirects=True)
    assert b'Payment successful!' in rv.data  
