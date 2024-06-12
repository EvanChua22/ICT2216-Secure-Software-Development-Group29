import os
from flask import Flask, flash, redirect, render_template, request, session, url_for
import sqlite3
from datetime import datetime
from matplotlib import use
from numpy import product
from werkzeug.utils import secure_filename
from functools import wraps
from werkzeug.security import check_password_hash
import sys

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Provide a secret key for session management
UPLOAD_FOLDER = "static/productImg"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    if "name" in session:
        role = session.get("role")
        if role == "admin":
            return redirect(url_for("enternew"))
        elif role == "user":
            return redirect(url_for("user_home"))
    return redirect(url_for("login"))


# Home Page route
@app.route("/user_home")
def user_home():
    if "name" and "user_id" in session and session.get("role") == "user":
        user_id = session["user_id"]
        return render_template("user_home.html", name=session["name"], user_id=user_id)
    else:
        return redirect(url_for("login"))


""" @app.route("/seller_home")
def seller_home():
    if 'name' in session and session.get('role') == 'seller':  
        return render_template("seller_home.html", name=session['name'])
    else:
        return redirect(url_for('login')) """


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Get the user input values from the input field
        name = request.form.get("name")
        password = request.form.get("password")
        role = request.form.get("role")

        # Connect to the database
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Retrieve the user's hashed password from the database
        cursor.execute("SELECT * FROM Users WHERE name = ?", (name,))
        result = cursor.fetchone()

        if result:
            user_id = result[0]
            stored_password = result[2]
            role = result[5]

            if stored_password == password:
                session["logged_in"] = True
                session["user_id"] = user_id
                session["name"] = name
                session["role"] = role

                if role == "admin":

                    return redirect(url_for("enternew"))
                elif role == "user":

                    return redirect(url_for("user_home"))

                else:
                    flash("Invalid identity", "error")
            else:
                flash("Invalid username or password", "error")
        else:
            flash("Invalid username or password", "error")

        # Close the connection to the database
        conn.close()
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/view_profile")
def view_profile():
    if "user_id" not in session:
        return redirect(url_for('login'))

    user_id = session["user_id"]
    
    # Connect to the SQLite database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Execute a query to fetch the user details
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    # Close the connection
    conn.close()

    if user:
        # Map the result to a dictionary for easier access in the template
        user_info = {
            'name': user[1],
            'email': user[4],
            'phoneNum': user[3],
        }
        return render_template('view_profile.html', user=user_info)
    else:
        flash('User not found', 'danger')
        return redirect(url_for('login'))

@app.route("/logout")
def logout():
    # Clear the user's session
    session.clear()
    # Redirect to the login page or home page after logout
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        name = request.form.get("name")
        password = request.form.get("password")
        phone_number = request.form.get("phoneNum")
        email = request.form.get("email")
        role = request.form.get("role")

        # Connect to the database
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                """ INSERT INTO Users (name, password, phoneNum, email, role, created_at) VALUES  (?, ?, ?, ?, ?, datetime('now'))""",
                (
                    name,
                    password,
                    phone_number,
                    email,
                    role,
                ),
            )
            conn.commit()
            conn.close()
            flash("Your account has been successfully created!", "Success")
            return redirect(url_for("login"))

        except Exception as e:
            # Handle database errors and display an error message
            conn.rollback()
            flash(
                "An error has occured during registration. Please try again later.",
                "error",
            )
            print("Error", e)
        return redirect(url_for("register"))
    else:
        return render_template("register.html")


def save_image_to_database(image):
    if image:
        # Extract filename from the image object
        filename = secure_filename(image.filename)
        filename_without_extension = os.path.splitext(filename)[0]
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image.save(filepath)
        return filename_without_extension
    else:
        return None


@app.route("/upload_product", methods=["GET", "POST"])
def upload_product():

    if request.method == "POST":

        if "user_id" in session:
            user_id = session["user_id"]
        else:
            flash("User not logged in. Please log in to upload a product.", "error")
            return redirect(url_for("login"))
        product_name = request.form["product_name"]
        description = request.form["description"]
        price = request.form["price"]
        size = request.form["size"]
        condition = request.form["condition"]
        quantity = request.form["quantity"]

        image = request.files["image"]
        image_url = save_image_to_database(image)

        # Connect to the database
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                """ INSERT INTO Products (user_id, product_name, description, price, size, condition, image_url, quantity, created_at,
                verified) VALUES  (? ,?, ?, ?, ?, ?, ?, ?, datetime('now'),0)""",
                (
                    user_id,
                    product_name,
                    description,
                    price,
                    size,
                    condition,
                    image_url,
                    quantity,
                ),
            )
            conn.commit()
            conn.close()
            flash("Your product has been successfully uploaded!", "Success")
            return redirect(url_for("upload_product"))

        except Exception as e:
            # Handle database errors and display an error message
            conn.rollback()
            flash(
                "An error has occured during uploading. Please try again later.",
                "error",
            )
            print("Error", e)
        return redirect(url_for("upload_product"))
    else:
        return render_template("upload_product.html")


# Route to form used to add a new user to the database
@app.route("/enternew")
def enternew():
    if "name" in session and session.get("role") == "admin":
        return render_template("user.html", name=session["name"])
    else:
        return redirect(url_for("login"))


# Route to add a new record (INSERT) user data to the database
@app.route("/addrec", methods=["POST", "GET"])
def addrec():
    # Data will be available from POST submitted by the form
    if request.method == "POST":
        try:
            name = request.form["name"]
            password = request.form["password"]
            phoneNum = request.form["phoneNum"]
            email = request.form["email"]
            role = request.form["role"]

            # Connect to SQLite3 database and execute the INSERT
            with sqlite3.connect("database.db") as con:
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO Users (name, password, phoneNum, email, role, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
                    (name, password, phoneNum, email, role),
                )

                con.commit()
                msg = "Record successfully added to database"
        except Exception as e:
            con.rollback()
            msg = "Error in the INSERT: " + str(e)

        finally:
            con.close()
            # Send the transaction message to result.html
            return render_template("result.html", msg=msg)


# Route to SELECT all data from the database and display in a table
@app.route("/list")
def list():
    # Connect to the SQLite3 datatabase and
    # SELECT rowid and all Rows from the users table.
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row

    cur = con.cursor()
    cur.execute("SELECT user_id, * FROM Users")

    rows = cur.fetchall()
    con.close()
    # Send the results of the SELECT to the list.html page
    return render_template("list.html", rows=rows)


# Route that will SELECT a specific row in the database then load an Edit form
@app.route("/edit", methods=["POST", "GET"])
def edit():
    if request.method == "POST":
        try:
            # Use the hidden input value of id from the form to get the user_id
            user_id = request.form["user_id"]
            # Connect to the database and SELECT a specific user_id
            con = sqlite3.connect("database.db")
            con.row_factory = sqlite3.Row

            cur = con.cursor()
            cur.execute("SELECT user_id, * FROM Users WHERE user_id = ?", (user_id,))

            rows = cur.fetchall()
        except Exception as e:
            user_id = None
            print("Error in the SELECT: " + str(e))
        finally:
            con.close()
            # Send the specific record of data to edit.html
            return render_template("edit.html", rows=rows)


# Route used to execute the UPDATE statement on a specific record in the database
@app.route("/editrec", methods=["POST", "GET"])
def editrec():
    # Data will be available from POST submitted by the form
    if request.method == "POST":
        try:
            # Use the hidden input value of id from the form to get the user_id
            user_id = request.form["user_id"]
            name = request.form["name"]
            password = request.form["password"]
            phoneNum = request.form["phoneNum"]
            email = request.form["email"]
            role = request.form["role"]

            # UPDATE a specific record in the database based on the user_id
            with sqlite3.connect("database.db") as con:
                cur = con.cursor()
                cur.execute(
                    "UPDATE Users SET name = ?, password = ?, phoneNum = ?, email = ?, role = ? WHERE user_id = ?",
                    (name, password, phoneNum, email, role, user_id),
                )

                con.commit()
                msg = "Record successfully edited in the database"
        except Exception as e:
            con.rollback()
            msg = "Error in the Edit: " + str(e)

        finally:
            con.close()
            # Send the transaction message to result.html
            return render_template("result.html", msg=msg)


# Route used to DELETE a specific record in the database
@app.route("/delete", methods=["POST", "GET"])
def delete():
    if request.method == "POST":
        try:
            # Use the hidden input value of id from the form to get the user_id
            user_id = request.form["user_id"]
            # Connect to the database and DELETE a specific record based on user_id
            with sqlite3.connect("database.db") as con:
                cur = con.cursor()
                cur.execute("DELETE FROM Users WHERE user_id = ?", (user_id,))

                con.commit()
                msg = "Record successfully deleted from the database"
        except Exception as e:
            con.rollback()
            msg = "Error in the DELETE: " + str(e)

        finally:
            con.close()
            # Send the transaction message to result.html
            return render_template("result.html", msg=msg)


# Route View all products
@app.route("/view_products")
def view_products():

    if "user_id" in session:
        user_id = session["user_id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, product_name, price, image_url FROM Products")
    products = cursor.fetchall()
    conn.close()

    # Converting the fetched data into a list of dictionaries
    products_list = []
    for product in products:
        product_dict = {
            "product_id": product[0],
            "product_name": product[1],
            "price": product[2],
            "image_url": product[3],
        }
        products_list.append(product_dict)

    return render_template(
        "view_products.html", products_list=products_list, user_id=user_id
    )


@app.route("/product_details/<int:product_id>")
def product_details(product_id):

    if "user_id" in session:
        user_id = session["user_id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Fetch product details from the database based on the product_id
    cursor.execute("SELECT * FROM Products WHERE product_id = ?", (product_id,))
    product_details = cursor.fetchone()

    # If product_details is not None, convert it to a dictionary for easy access in the template
    if product_details:
        product_dict = {
            "product_id": product_details[0],
            "user_id": product_details[1],
            "product_name": product_details[2],
            "description": product_details[3],
            "price": product_details[4],
            "size": product_details[5],
            "condition": product_details[6],
            "image_url": product_details[7],
            "quantity": product_details[8],
            "created_at": product_details[9],
            "verified": product_details[10],
        }
    else:
        product_dict = None

    conn.close()

    # Pass the product details to the product_details.html template
    return render_template(
        "product_details.html",
        product=product_dict,
        reviews=products_reviews(product_id),
        user_id=user_id,
        product_id=product_id,
    )


def products_reviews(product_id):
    user_id = session.get("user_id")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # Fetch reviews
    cursor.execute(
        """SELECT r.review_id, r.rating, r.comment, r.created_at, u.name 
                          FROM Reviews r JOIN Users u ON r.user_id = u.user_id 
                          WHERE r.product_id = ? ORDER BY r.created_at DESC""",
        (product_id,),
    )
    reviews = cursor.fetchall()
    print(reviews)
    review_list = [
        {
            "review_id": row[0],
            "rating": row[1],
            "comment": row[2],
            "created_at": row[3],
            "user_name": row[4],
        }
        for row in reviews
    ]

    conn.close()

    return review_list


@app.route("/my_products")
def my_products():

    if "user_id" in session:
        user_id = session["user_id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Products where user_id = ?", (user_id,))
    products = cursor.fetchall()

    conn.close()

    # Converting the fetched data into a list of dictionaries
    products_list = []
    for product in products:
        product_dict = {
            "product_id": product[0],
            "product_name": product[2],
            "price": product[4],
            "image_url": product[7],
        }
        products_list.append(product_dict)

    return render_template(
        "my_products.html", products_list=products_list, user_id=user_id
    )


@app.route("/my_products_details/<int:product_id>")
def my_products_details(product_id):
    user_id = session.get("user_id")
    review_list = my_products_reviews(product_id)
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    product_dict = None

    # Fetch product details
    cursor.execute("SELECT * FROM Products WHERE product_id = ?", (product_id,))
    product_details = cursor.fetchone()
    if product_details:
        product_dict = {
            "product_id": product_details[0],
            "user_id": product_details[1],
            "product_name": product_details[2],
            "description": product_details[3],
            "price": product_details[4],
            "size": product_details[5],
            "condition": product_details[6],
            "image_url": product_details[7],
            "quantity": product_details[8],
            "created_at": product_details[9],
            "verified": product_details[10],
        }

    conn.close()
    print(product_details, file=sys.stderr)
    print(review_list, file=sys.stderr)

    return render_template(
        "my_products_details.html",
        product=product_dict,
        reviews=review_list,
        user_id=user_id,
        product_id=product_id,
    )


def my_products_reviews(product_id):
    user_id = session.get("user_id")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # Fetch reviews
    cursor.execute(
        """SELECT r.review_id, r.rating, r.comment, r.created_at, u.name 
                          FROM Reviews r JOIN Users u ON r.user_id = u.user_id 
                          WHERE r.product_id = ? ORDER BY r.created_at DESC""",
        (product_id,),
    )
    reviews = cursor.fetchall()
    print(reviews)
    review_list = [
        {
            "review_id": row[0],
            "rating": row[1],
            "comment": row[2],
            "created_at": row[3],
            "user_name": row[4],
        }
        for row in reviews
    ]

    conn.close()

    return review_list


@app.route("/product_review/<int:product_id>")
def product_review(product_id):
    # Ensure user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Fetch product details to display on the review page
    cursor.execute("SELECT * FROM Products WHERE product_id = ?", (product_id,))
    product_details = cursor.fetchone()
    conn.close()

    # Convert product_details to a dictionary
    if product_details:
        product_dict = {
            "product_id": product_details[0],
            "product_name": product_details[2],
        }
    else:
        product_dict = None

    return render_template("product_review.html", product=product_dict)


@app.route("/submit_review/<int:product_id>", methods=["POST"])
def submit_review(product_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    rating = request.form["rating"]
    comment = request.form["comment"]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Insert the new review into the Reviews table
    cursor.execute(
        """
        INSERT INTO Reviews (product_id, user_id, rating, comment, created_at)
        VALUES (?, ?, ?, ?, ?)
    """,
        (product_id, user_id, rating, comment, created_at),
    )

    conn.commit()
    conn.close()

    return redirect(url_for("view_products"))


@app.route("/delete_product/<int:product_id>", methods=["POST"])
def delete_product(product_id):

    if "user_id" not in session:
        return "You must be logged in to delete a product."

    # Retrieve user's ID from session
    user_id = session["user_id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM Products WHERE product_id = ? AND user_id = ?",
        (product_id, user_id),
    )
    product = cursor.fetchone()

    if product:
        try:
            # Delete the product from the database
            cursor.execute("DELETE FROM Products WHERE product_id = ?", (product_id,))
            conn.commit()
            msg = "Product successfully deleted from the database"
        except Exception as e:
            conn.rollback()
            msg = "Error in the DELETE: " + str(e)
        finally:
            conn.close()
            # Redirect to homepage or any other appropriate page after deletion
            return render_template("result.html", msg=msg)
    else:
        conn.close()
        return "Product not found or you don't have permission to delete it."


def toggle_verified(product_id):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Retrieve the current verified status
        cursor.execute(
            "SELECT verified FROM products WHERE product_id = ?", (product_id,)
        )
        current_status = cursor.fetchone()

        if current_status is not None:
            # Toggle the verified status
            new_status = 0 if current_status[0] else 1

            # Update the verified status of the product
            cursor.execute(
                """
                UPDATE products
                SET verified = ?
                WHERE product_id = ?
                """,
                (new_status, product_id),
            )

            # Commit the changes and close the connection
            conn.commit()

        conn.close()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")


@app.route("/toggle_verified/<int:product_id>", methods=["POST"])
def toggle_verified_route(product_id):
    # Call the toggle_verified function
    toggle_verified(product_id)
    return redirect(url_for("product_details", product_id=product_id))


if __name__ == "__main__":
    app.run(debug=True)
