from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# Home Page route
@app.route("/")
def home():
    return render_template("home.html")

# Route to form used to add a new user to the database
@app.route("/enternew")
def enternew():
    return render_template("user.html")

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

if __name__ == '__main__':
    app.run(debug=True)