import unittest
import tempfile
import os
import sqlite3
from app import app, sanitize_input, ph


class TestRegister(unittest.TestCase):

    def setUp(self):
        # Create a temporary file to use as a test database
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + self.db_path
        self.client = app.test_client()

        # Initialize the database schema
        with app.app_context():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
            CREATE TABLE Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                phoneNum TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            )
            conn.commit()
            conn.close()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_register_post(self):
        # Prepare the data to be sent in the POST request
        data = {
            "name": "testuser",
            "password": "testpassword",
            "phoneNum": "1234567890",
            "email": "testuser@example.com",
            "role": "user",
        }

        # Send POST request to /register
        response = self.client.post("/register", data=data, follow_redirects=True)

        # Check that the response contains the success message
        self.assertIn(b"Your account has been successfully created!", response.data)

        # Check that the user was added to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE email = ?", (data["email"],))
        user = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(user)
        self.assertEqual(user[1], "testuser")  # name
        self.assertTrue(ph.verify("testpassword", user[2]))  # password
        self.assertEqual(user[3], "1234567890")  # phoneNum
        self.assertEqual(user[4], "testuser@example.com")  # email
        self.assertEqual(user[5], "user")  # role

    def test_register_post_invalid_email(self):
        # Prepare the data with an invalid email
        data = {
            "name": "testuser",
            "password": "testpassword",
            "phoneNum": "1234567890",
            "email": "invalid-email",
            "role": "user",
        }

        # Send POST request to /register
        response = self.client.post("/register", data=data, follow_redirects=True)

        # Check that the response contains the error message
        self.assertIn(
            b"An error has occured during registration. Please try again later.",
            response.data,
        )

        # Check that no user was added to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE email = ?", (data["email"],))
        user = cursor.fetchone()
        conn.close()

        self.assertIsNone(user)


if __name__ == "__main__":
    unittest.main()
