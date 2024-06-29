import unittest
import tempfile
import os
from flask import Flask
from app import app, db


class TestRegister(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + self.db_path
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

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
        with app.app_context():
            user = db.session.execute(
                "SELECT * FROM Users WHERE email = :email",
                {"email": "testuser@example.com"},
            ).fetchone()
            self.assertIsNotNone(user)
            self.assertEqual(user["name"], "testuser")


if __name__ == "__main__":
    unittest.main()
