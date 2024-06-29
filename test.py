import unittest
from app import app


class TestSearchProducts(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def test_search_products(self):
        query = "Apple"
        response = self.app.get(f"/search_products?query={query}")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Apple", response.data)  # Check if "Apple" is in the response
        self.assertNotIn(
            b"Banana", response.data
        )  # Check if "Banana" is not in the response
        self.assertNotIn(
            b"Orange", response.data
        )  # Check if "Orange" is not in the response


if __name__ == "__main__":
    unittest.main()
