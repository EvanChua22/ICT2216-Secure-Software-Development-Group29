import os
import sqlite3
import pytest
from app import app, ph  

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
    cursor.execute('''CREATE TABLE IF NOT EXISTS Reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users (id),
        FOREIGN KEY (product_id) REFERENCES Products (id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
    )''')
    conn.commit()
    cursor.execute('''INSERT INTO Users (name, password, phoneNum, email, role)
                      VALUES (?, ?, ?, ?, ?)''', ('testuser', ph.hash('password123'), '1234567890', 'test@example.com', 'user'))
    conn.commit()
    conn.close()

def test_add_to_cart(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1  # Simulate a logged-in user

    rv = client.post('/add_to_cart', data={
        'product_id': 1,
        'quantity': 2
    }, follow_redirects=True)
    assert b'Product added to cart!' in rv.data  

def test_remove_from_cart(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1  # Simulate a logged-in user

    # First, add a product to the cart
    client.post('/add_to_cart', data={
        'product_id': 1,
        'quantity': 2
    }, follow_redirects=True)

    # Then, remove the product from the cart
    rv = client.post('/remove_from_cart', data={
        'cart_item_id': 1
    }, follow_redirects=True)
    assert b'Product removed from cart!' in rv.data  

def test_update_cart(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1  # Simulate a logged-in user

    # First, add a product to the cart
    client.post('/add_to_cart', data={
        'product_id': 1,
        'quantity': 2
    }, follow_redirects=True)

    # Then, update the quantity of the product in the cart
    rv = client.post('/update_cart', data={
        'cart_item_id': 1,
        'quantity': 5
    }, follow_redirects=True)
    assert b'Cart updated!' in rv.data  
