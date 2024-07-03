# python create_table.py

import sqlite3

conn = sqlite3.connect('database.db')
print("Connected to database successfully")

# Create tables
conn.execute('''
CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY,
    name VARCHAR(45),
    password VARCHAR(45),
    phoneNum VARCHAR(45),
    email VARCHAR(45),
    role VARCHAR(10),
    created_at DATETIME
)
''')
print("Created table Users successfully!")

conn.execute('''
CREATE TABLE Products (
    product_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    product_name VARCHAR(45),
    description VARCHAR(45),
    price DECIMAL(10,2),
    size VARCHAR(10),
    condition VARCHAR(20),
    image_blob BLOB,
    quantity INTEGER,
    created_at DATETIME,
    verified BOOLEAN,
    FOREIGN KEY(user_id) REFERENCES Users(user_id)
)
''')
print("Created table Products successfully!")

conn.execute('''
CREATE TABLE Orders (
    order_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    order_date DATETIME,
    total_amount DECIMAL(10,2),
    status VARCHAR(20),
    tracking_num VARCHAR(50),
    shipping_address VARCHAR(255),
    created_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES Users(user_id)
)
''')
print("Created table Orders successfully!")

conn.execute('''
CREATE TABLE Order_Items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    price DECIMAL(10,2),
    FOREIGN KEY(order_id) REFERENCES Orders(order_id),
    FOREIGN KEY(product_id) REFERENCES Products(product_id)
)
''')
print("Created table Order_Items successfully!")

conn.execute('''
CREATE TABLE Payments (
    payment_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    payment_amt DECIMAL(10,2),
    payment_method INTEGER,
    payment_date DATETIME,
    status VARCHAR(20),
    FOREIGN KEY(order_id) REFERENCES Orders(order_id)
)
''')
print("Created table Payments successfully!")

conn.execute('''
CREATE TABLE Reviews (
    review_id INTEGER PRIMARY KEY,
    product_id INTEGER,
    user_id INTEGER,
    rating INTEGER,
    created_at DATETIME,
    comment TEXT,
    FOREIGN KEY(product_id) REFERENCES Products(product_id),
    FOREIGN KEY(user_id) REFERENCES Users(user_id)
)
''')
print("Created table Reviews successfully!")

conn.execute('''
CREATE TABLE Shopping_Cart (
    cart_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES Users(user_id)
)
''')
print("Created table Shopping_Cart successfully!")

conn.execute('''
CREATE TABLE Cart_Items (
    cart_item_id INTEGER PRIMARY KEY,
    cart_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY(cart_id) REFERENCES Shopping_Cart(cart_id),
    FOREIGN KEY(product_id) REFERENCES Products(product_id)
)
''')
print("Created table Cart_Items successfully!")

conn.execute('''
CREATE TABLE Chats (
    chat_id INTEGER PRIMARY KEY,
    user1_id INTEGER,
    user2_id INTEGER,
    FOREIGN KEY(user1_id) REFERENCES Users(user_id),
    FOREIGN KEY(user2_id) REFERENCES Users(user_id)
)
''')
print("Created table Chats successfully!")

conn.execute('''
CREATE TABLE Messages (
    message_id INTEGER PRIMARY KEY,
    chat_id INTEGER,
    sender_id INTEGER,
    content TEXT,
    timestamp TIMESTAMP,
    FOREIGN KEY(chat_id) REFERENCES Chats(chat_id),
    FOREIGN KEY(sender_id) REFERENCES Users(user_id)
)
''')
print("Created table Messages successfully!")

# Close the connection
conn.close()
print("Closed connection to database successfully!")
