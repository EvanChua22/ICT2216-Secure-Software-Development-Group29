# test_cart.py

import os
import sqlite3
import pytest
from flask import session
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.secret_key = 'secret'  # Required for session handling

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
    
    # Create Users table if not exists
    cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        phoneNum TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
    )''')
    
    # Create Products table if not exists
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
    
    # Create Shopping_Cart table if not exists
    cursor.execute('''CREATE TABLE IF NOT EXISTS Shopping_Cart (
         cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
         user_id INTEGER,
         FOREIGN KEY(user_id) REFERENCES Users(user_id)
    )''')
    
    # Create Cart_Items table if not exists
    cursor.execute('''CREATE TABLE IF NOT EXISTS Cart_Items (
        cart_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cart_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        FOREIGN KEY(cart_id) REFERENCES Shopping_Cart(cart_id),
        FOREIGN KEY(product_id) REFERENCES Products(product_id)
    )''')
    
    # Create Reviews table if not exists
    cursor.execute('''CREATE TABLE IF NOT EXISTS Reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users (user_id),
        FOREIGN KEY (product_id) REFERENCES Products (product_id)
    )''')
    
    # Insert an example user for testing with plain password (you can hash it if needed)
    cursor.execute('''INSERT INTO Users (name, password, phoneNum, email, role)
                      VALUES (?, ?, ?, ?, ?)''', ('testuser', 'password123', '1234567890', 'test@example.com', 'user'))
    
    # Insert example products
    cursor.execute('''INSERT INTO Products (product_name, price, description)
                      VALUES (?, ?, ?)''', ('Product A', 10.99, 'Example product A description'))
    cursor.execute('''INSERT INTO Products (product_name, price, description)
                      VALUES (?, ?, ?)''', ('Product B', 19.99, 'Example product B description'))
    
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
