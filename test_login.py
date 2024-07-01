import os
import sqlite3
import pytest
from argon2 import PasswordHasher
from app import app, init_db

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
            init_db()  # Initialize the database with Users and logs tables
        yield client

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Create Users table if not exists
    cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        phoneNum TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
    )''')
    
    # Create Logs table if not exists
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        user_id INTEGER,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
    )''')
    
    # Insert an example user for testing with hashed password
    ph = PasswordHasher()
    hashed_password = ph.hash("password123")
    cursor.execute('''INSERT INTO Users (name, password, phoneNum, email, role)
                      VALUES (?, ?, ?, ?, ?)''', ('testuser', hashed_password, '1234567890', 'test@example.com', 'user'))
    
    conn.commit()
    conn.close()

def test_login_success(client):
    rv = client.post('/login', data={
        'name': 'testuser',
        'password': 'password123',
        'role': 'user'
    }, follow_redirects=True)
    assert b'Welcome, testuser!' in rv.data  

def test_login_failure(client):
    rv = client.post('/login', data={
        'name': 'testuser',
        'password': 'wrongpassword',
        'role': 'user'
    }, follow_redirects=True)
    assert b'Invalid username or password' in rv.data

def test_login_nonexistent_user(client):
    rv = client.post('/login', data={
        'name': 'nonexistent',
        'password': 'password123',
        'role': 'user'
    }, follow_redirects=True)
    assert b'Invalid username or password' in rv.data
