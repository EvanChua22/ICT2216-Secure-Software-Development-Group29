from flask import (Flask, flash, redirect, render_template, request, session, url_for)
import sqlite3
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Provide a secret key for session management

@app.route("/")
def index():
    if 'name' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('enternew'))
        elif role == 'user':
            return redirect(url_for('user_home'))
    return redirect(url_for('login'))


# Home Page route
@app.route("/user_home")
def user_home():
    if 'name' in session and session.get('role') == 'user':  
        return render_template("user_home.html", name=session['name'])
    else:
        return redirect(url_for('login'))

''' @app.route("/seller_home")
def seller_home():
    if 'name' in session and session.get('role') == 'seller':  
        return render_template("seller_home.html", name=session['name'])
    else:
        return redirect(url_for('login')) '''

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Get the user input values from the input field
        name = request.form.get("name")
        password = request.form.get("password")
        role = request.form.get("role")

        # Connect to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Retrieve the user's hashed password from the database
        cursor.execute("SELECT * FROM Users WHERE name = ?", (name,))
        result = cursor.fetchone()

        if result :
            stored_password = result[2]
            role = result[5]

            if stored_password == password:
                if role == role:
                    session['name'] = name
                    session['role'] = role
                    if role == "admin":
                        return redirect(url_for('enternew'))
                    elif role == "user":
                        return redirect(url_for('user_home'))
                        
                else:
                    flash('Invalid identity', 'error')
            else:
                flash('Invalid username or password', 'error')
        else:
            flash('Invalid username or password', 'error')

        # Close the connection to the database
        conn.close()
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route("/logout")
def logout():
    # Clear the user's session
    session.clear()
    # Redirect to the login page or home page after logout
    return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        name = request.form.get("name")
        password = request.form.get("password")
        phone_number = request.form.get("phoneNum")
        email = request.form.get("email")        
        role = request.form.get("role")

        # Connect to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute(
                ''' INSERT INTO Users (name, password, phoneNum, email, role, created_at) VALUES  (?, ?, ?, ?, ?, datetime('now'))''',
                (
                    name,
                    password,
                    phone_number,
                    email,
                    role,
                )
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


# Route to form used to add a new user to the database
@app.route("/enternew")
def enternew():
    if 'name' in session and session.get('role') == 'admin':
        return render_template("user.html", name=session['name'])
    else:
        return redirect(url_for('login'))
    

# Route to add a new record (INSERT) user data to the database
@app.route("/addrec", methods=['POST', 'GET'])
def addrec():
    # Data will be available from POST submitted by the form
    if request.method == 'POST':
        try:
            name = request.form['name']
            password = request.form['password']
            phoneNum = request.form['phoneNum']
            email = request.form['email']
            role = request.form['role']

            # Connect to SQLite3 database and execute the INSERT
            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("INSERT INTO Users (name, password, phoneNum, email, role, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))", (name, password, phoneNum, email, role))

                con.commit()
                msg = "Record successfully added to database"
        except Exception as e:
            con.rollback()
            msg = "Error in the INSERT: " + str(e)

        finally:
            con.close()
            # Send the transaction message to result.html
            return render_template('result.html', msg=msg)

# Route to SELECT all data from the database and display in a table      
@app.route('/list')
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
@app.route("/edit", methods=['POST', 'GET'])
def edit():
    if request.method == 'POST':
        try:
            # Use the hidden input value of id from the form to get the user_id
            user_id = request.form['user_id']
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
@app.route("/editrec", methods=['POST', 'GET'])
def editrec():
    # Data will be available from POST submitted by the form
    if request.method == 'POST':
        try:
            # Use the hidden input value of id from the form to get the user_id
            user_id = request.form['user_id']
            name = request.form['name']
            password = request.form['password']
            phoneNum = request.form['phoneNum']
            email = request.form['email']
            role = request.form['role']

            # UPDATE a specific record in the database based on the user_id
            with sqlite3.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("UPDATE Users SET name = ?, password = ?, phoneNum = ?, email = ?, role = ? WHERE user_id = ?", (name, password, phoneNum, email, role, user_id))

                con.commit()
                msg = "Record successfully edited in the database"
        except Exception as e:
            con.rollback()
            msg = "Error in the Edit: " + str(e)

        finally:
            con.close()
            # Send the transaction message to result.html
            return render_template('result.html', msg=msg)

# Route used to DELETE a specific record in the database    
@app.route("/delete", methods=['POST', 'GET'])
def delete():
    if request.method == 'POST':
        try:
             # Use the hidden input value of id from the form to get the user_id
            user_id = request.form['user_id']
            # Connect to the database and DELETE a specific record based on user_id
            with sqlite3.connect('database.db') as con:
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
            return render_template('result.html', msg=msg)
        
# Route View all products  
@app.route('/view_products')
def view_products():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, product_name, price, image_url FROM Products")
    products = cursor.fetchall()
    conn.close()
    
    # Converting the fetched data into a list of dictionaries
    products_list = []
    for product in products:
        product_dict = {
            'product_id': product[0],
            'product_name': product[1],
            'price': product[2],
            'image_url': product[3]
        }
        products_list.append(product_dict)
    
    return render_template('view_products.html', products_list=products_list)

@app.route('/product_details/<int:product_id>')
def product_details(product_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Fetch product details from the database based on the product_id
    cursor.execute("SELECT * FROM Products WHERE product_id = ?", (product_id,))
    product_details = cursor.fetchone()

    # If product_details is not None, convert it to a dictionary for easy access in the template
    if product_details:
        product_dict = {
            'product_id': product_details[0],
            'user_id': product_details[1],
            'product_name': product_details[2],
            'description': product_details[3],
            'price': product_details[4],
            'size': product_details[5],
            'condition': product_details[6],
            'image_url': product_details[7],
            'quantity': product_details[8],
            'created_at': product_details[9],
            'verified': product_details[10]
        }
    else:
        product_dict = None

    conn.close()
    
    # Pass the product details to the product_details.html template
    return render_template('product_details.html', product=product_dict)


if __name__ == '__main__':

    app.run(debug=True)