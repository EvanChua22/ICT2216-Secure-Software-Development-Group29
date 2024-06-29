import os
import sqlite3
import pytest
from app import app, sanitize_input

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
    cursor.execute('''CREATE TABLE Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        phoneNum TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
    )''')
    conn.commit()
    conn.close()

def test_sanitize_input():
    assert sanitize_input("Hello <script>") == "Hello script"
    assert sanitize_input("john.doe@example.com", "email") == "john.doe@example.com"
    assert sanitize_input("123-456-7890", "phone") == "1234567890"
    assert sanitize_input("Password@123", "password") == "Password@123"

def test_register(client):
    rv = client.post('/register', data={
        'name': 'testuser',
        'password': 'password123',
        'phoneNum': '1234567890',
        'email': 'test@example.com',
        'role': 'user'
    }, follow_redirects=True)
    assert b'Your account has been successfully created!' in rv.data

def test_register_duplicate(client):
    # Register a user
    client.post('/register', data={
        'name': 'testuser',
        'password': 'password123',
        'phoneNum': '1234567890',
        'email': 'test@example.com',
        'role': 'user'
    }, follow_redirects=True)

    # Try to register the same user again
    rv = client.post('/register', data={
        'name': 'testuser',
        'password': 'password123',
        'phoneNum': '1234567890',
        'email': 'test@example.com',
        'role': 'user'
    }, follow_redirects=True)
    assert b'An error has occured during registration. Please try again later.' in rv.data
