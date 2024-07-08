import os
from flask import Flask, flash, make_response, redirect, render_template, request, session, url_for
import sqlite3
from datetime import datetime, timedelta, timezone
from matplotlib import use
from werkzeug.utils import secure_filename
from functools import wraps
from werkzeug.security import check_password_hash
import sys
import re
import random
import string
import smtplib
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from werkzeug.security import generate_password_hash
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import dns.resolver
from flask_caching import Cache
from flask_caching.backends import FileSystemCache
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import secrets

# For logging to a file
import logging
from logging.handlers import RotatingFileHandler

#imports for rate limiting 
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import warnings
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="Using the in-memory storage for tracking rate limits as no storage was explicitly specified."
)

app = Flask(__name__)
# TODO Need to hide this secret_key also. 
app.secret_key = "your_secret_key"  # Provide a secret key for session management
UPLOAD_FOLDER = "static/productImg"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max size
serializer = URLSafeTimedSerializer(app.secret_key)

# Configuring dB for Session Management.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sessions.db'  # You can use any other database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(app.root_path, '../database.db'))
print(DATABASE_PATH)

# Initialize the Argon2id password hasher
# ph = PasswordHasher()

ph = PasswordHasher(
    time_cost=5,  # Number of iterations (default is 2)
    memory_cost=7168,  # Memory usage in KiB (default is 102400, 100 MiB)
    parallelism=1,  # Number of parallel threads (default is 8)
    hash_len=32,  # Length of the hash (default is 16 bytes)
    salt_len=16  # Length of the random salt (default is 16 bytes)
)

# Initialize the Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)


# Create and configure the Flask application
# app = Flask(__name__)

# Setup logging to a file
log_path = '/var/log/my_flask_app/app.log'
os.makedirs(os.path.dirname(log_path), exist_ok=True)
handler = RotatingFileHandler(log_path, maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)


# Redirect rate limit error to its own html
@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template("rate_limit_exceeded.html"), 429

# Secure Session Cookies
app.config.update(
    SESSION_COOKIE_HTTPONLY=True, # Cookie can only be modified by http, not javascript. prevents XSS attacks.
    SESSION_COOKIE_SECURE=True,   #set this to true when site is using HTTPS #Ensures that the session cookie is only sent over HTTPS
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_REFRESH_EACH_REQUEST = False,
    SESSION_TYPE = 'sqlalchemy',
    SESSION_SQLALCHEMY = SQLAlchemy(app),
    SESSION_PERMANENT = True, 
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=15)  #Set session to 1 hour can be changed if needed
)


# This implements Session Timeout and is set to 1 hour
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)
    session.modified = True


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def otp_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in") or not session.get("otp_verified"):
            session.clear()  # Clear the session if trying to access without OTP verification
            flash("Please log in again.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function



@app.route("/")
def index():
    app.logger.info("Visited the main page! %s","oops")
    if "name" in session:
        role = session.get("role")
        if role == "admin":
            return redirect(url_for("list"))
        elif role == "user":
            return redirect(url_for("user_home"))
    return redirect(url_for("login"))


# Home Page route
@app.route("/user_home")
@otp_required
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


def sanitize_input(input_data, input_type="text"):
    if input_type == "text":
        return re.sub(r"[^\w\s]", "", input_data)
    elif input_type == "email":
        return re.sub(r"[^\w\s@.-]", "", input_data)
    elif input_type == "password":
        # Passwords should be hashed and salted, but if you want to allow special characters, sanitize differently
        # return re.sub(r"[^\w\s@#$%^&*()_+=-]", "", input_data)
        return input_data
    elif input_type == "phone":
        return re.sub(r"[^\d]", "", input_data)
    return input_data


@app.route("/unlock", methods=["GET", "POST"])
def unlock():
    name = request.form.get('name')

    try:
        conn = sqlite3.connect("../database.db")
        cursor = conn.cursor()
        # Resets login_attempts to 0, unlocking account. 
        cursor.execute("UPDATE Users SET login_attempts = 0 WHERE name = ?", (name,))
        conn.commit()
    except:
        print('fail')

    return redirect(request.referrer)

# Only allow POST for login, else credentials will be visible in URL.
@app.route("/login", methods=["GET","POST"])
@limiter.limit("8 per minute")  # Limit login attempts to 8 per minute
def login():
    app.logger.error("Visited the main page! %s","oops")
    if request.method == "POST":
        # Get the user input values from the input field
        app.logger.info("Following method was used to vist: %s", "POST")
        name = sanitize_input(request.form.get("name"))
        password = sanitize_input(request.form.get("password"), input_type='password')
       
        # Connect to the database
        conn = sqlite3.connect("../database.db")
        cursor = conn.cursor()

        app.logger.info("Connected to the following dB: %s", "database.db")
        # TODO TO DELETE. IF THE ACCOUNT U USING FOR TESTING GETS LOCKED. UNCOMMENT BELOW 2 LINES AND TRY LOGIN WITH
        # THAT USERNAME. WILL RESET LOGIN_ATTEMPT COUNTER TO 0
        # cursor.execute("UPDATE Users SET login_attempts = 1 WHERE name = ?", (name,))
        # conn.commit()
        # END OF DELETE.
        
        # Checking if account has reached failed login attempts.
        login_attempts = cursor.execute("SELECT login_attempts FROM Users WHERE name = ?", (name,) ).fetchone()
        app.logger.info("Read that this account has this many failed logins: %s", login_attempts)
        
        if ( isinstance(login_attempts,int) and login_attempts[0] >= 5 ):
            flash("Your account has been locked. Contact An Admin To Unlock Your Account")
            # Does not continue onto validation for locked accounts. 
            return render_template('login.html')
        elif (not isinstance(login_attempts,int) ):
            try:
                cursor.execute("UPDATE Users SET login_attempts = 1 WHERE name = ?", (name,))
            except:
                print("works")
       
            

        # Retrieve the user's hashed password from the database
        cursor.execute("SELECT * FROM Users WHERE name = ?", (name,))
        result = cursor.fetchone()
        app.logger.info("Currently trying to login: %s", result)

        if result:
            user_id = result[0]
            stored_password = result[2]
            # role = result[5]

            try:
                # Verify the password using Argon2id
                ph.verify(stored_password, password)

                # Password verification succeeded
                # Clear the session first to prevent the same session being used
                session.clear()
                session["logged_in"] = True
                session["user_id"] = user_id
                session["name"] = name
                # session["role"] = role
                session["otp_verified"] = False
             

                # Reset the Login_attempts counter
                try:
                    cursor.execute("UPDATE Users SET login_attempts = 0 WHERE name = ?", (name,))
                    conn.commit()
                except Exception as e:
                    app.logger.error("Error Occured when trying to reset failed logins attempt. %s", e)
                   

                if name == "Admin2":
                    session["role"] = "admin"
                    return redirect(url_for("list"))
                else:
                    session["role"] = "user"
                    # When doing testing and need to keep logging in, can just comment this and redirect to 'user_home' instead
                    # return redirect(url_for("user_home"))
                    if(cursor.execute("SELECT is_verified FROM Users WHERE name = ?", (name,)).fetchone()[0]  == 0 ):
                        flash("Your account is still not verified. You can only login after verifying your Email. \n Check Your Inbox, As Well As Your Spam Folder.")
                        # return redirect(url_for("verifyAccount"))
                    else:
                        return redirect(url_for("sendOTP"))
            except VerifyMismatchError:
                # Password verification failed
                flash("Invalid username or password", "error")

                # Increase Failed Login in by 1
                try:
                    cursor.execute("UPDATE Users SET login_attempts = login_attempts + 1 WHERE name = ?", (name,))
                    
                except Exception as e:
                    app.logger.error("Failed to add one failed login attempt: %s", e)


        else:
            flash("Invalid username or password", "error")

        # Close the connection to the database
        conn.commit()
        conn.close()
        create_log(event_type="Login", user_id=name, details=name + " logged in")
        return redirect(url_for("login"))

    return render_template("login.html")

# Multi-Factor Authentication
def generate_otp():
    return ''.join(secrets.choice(string.digits) for _ in range(6))


def send_email(recipient_email, subject, body):
    smtp_server = 'smtp.outlook.com'
    smtp_port = 587
    # TODO Need to find a way to hide. 
    smtp_username = 'GrannyVintageThread@outlook.com'
    smtp_password = 'GrannyThread1965'

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(smtp_username, recipient_email, message)

    except smtplib.SMTPAuthenticationError as auth_error:
        print(f"SMTP Authentication Error: {auth_error}")
    except Exception as e:
        print(f"Error sending email: {e}")


def emailValidity(email):
    # Define a regular expression for validating an Email
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(email_regex, email) is None:
        return False
    
    # Extract the domain part of the email
    domain = email.split('@')[1]
    
    # Perform DNS lookup for the domain
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
        return False


@app.route("/sendOTP")
@limiter.limit("8 per minute") 
def sendOTP():
    if not session.get("logged_in") or session.get("otp_verified"):
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    name = session.get("name")

    if not user_id or not name:
        flash("User not authenticated", "error")
        return redirect(url_for("login"))
    if "otp" not in session or request.args.get("resend") == "true":
        # Generate OTP
        otp = generate_otp()

        # Store OTP in session
        session["otp"] = otp
        session["otp_timestamp"] = datetime.now(timezone.utc)

        # Retrieve user email from the database
        conn = sqlite3.connect("../database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM Users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            email = result[0]
            # Send OTP via email
            send_email(email, "Your OTP for Login", f"We've received a request to login to your account. Please use the following One-Time Password: {otp} This OTP is valid for the next 1 minute. ")
            # might need to check spam folder 
            flash("OTP has been sent to your email.", "success")
        else:
            flash("Failed to retrieve user email.", "error")
    else:
        flash("OTP already sent. Please check your email.", "info")
    return render_template("sendOTP.html")

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    try: 
        user_otp = ''.join([request.form.get(f'otp{i}') for i in range(1, 7)])
        session_otp = session.get("otp")
        otp_timestamp = session.get("otp_timestamp")

        if user_otp and session_otp and user_otp == session_otp:
            # Check if OTP is expired
            if datetime.now(timezone.utc) - otp_timestamp < timedelta(minutes=1):
                session.pop("otp", None)
                session.pop("otp_timestamp", None)
                session["otp_verified"] = True  # Mark OTP as verified
                flash("Login successful!", "success")
                return redirect(url_for("user_home"))
            else:
                flash("OTP has expired. Please request a new one.", "error")
        else:
            flash("Invalid OTP. Please try again.", "error")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
    return redirect(url_for("sendOTP"))

@app.route("/view_profile")
def view_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Connect to the SQLite database
    conn = sqlite3.connect("../database.db")
    cursor = conn.cursor()

    # Execute a query to fetch the user details
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    # Close the connection
    conn.close()

    if user:
        # Map the result to a dictionary for easier access in the template
        user_info = {
            "name": user[1],
            "email": user[4],
            "phoneNum": user[3],
        }
        return render_template("view_profile.html", user=user_info)
    else:
        flash("User not found", "danger")
        return redirect(url_for("login"))

# Change Password
@app.route('/changePass', methods=['POST'])
def changePass():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_new_password = request.form['confirm_new_password']

    if new_password != confirm_new_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('view_profile', error="password_mismatch"))

    conn = sqlite3.connect("../database.db")
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM Users WHERE user_id = ?', (user_id,)).fetchone()

    if not user or not ph.verify(user[2], current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('view_profile', error="password_incorrect"))

    new_password_hash = ph.hash(new_password)
    conn.execute('UPDATE Users SET password = ? WHERE user_id = ?', (new_password_hash, user_id))
    conn.commit()
    conn.close()

    flash('Password successfully changed.', 'success')
    return redirect(url_for('view_profile'))


# Forgot Password Service
@app.route("/forgotPass", methods=["GET", "POST"])
@limiter.limit("8 per minute")
def forgotPass():
    if request.method == 'POST':
        email = request.form['email']
        
        # Check if email is valid
        if not emailValidity(email):
            flash('Invalid email address format.', 'error')
            return redirect(url_for('forgotPass'))
        
        # Execute raw SQL query using sqlite3
        conn = sqlite3.connect("../database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE email = ?", (email,))
        user_row = cursor.fetchone()
        conn.close()
        
        if user_row:
            # Assuming user_row has (id, email, password) structure
            user = {
                'user_id': user_row[0],
                'email': user_row[4],
                'password': user_row[2]
            }
            # Generate a token and send email
            token = serializer.dumps(email, salt='password-reset-salt')
            reset_url = url_for('resetPass', token=token, _external=True)
            subject = 'Password Reset Request'
            body = f'''To reset your password, visit the following link:
                        {reset_url}
                        If you did not make this request, simply ignore this email and no changes will be made.
                        '''
            send_email(user['email'], subject, body)
            flash('A password reset link has been sent to your email.', 'info')
        else:
            # gives generic msg even if email is not associated with any account
            # without actually sending
            flash('A password reset link has been sent to your email.', 'info')
        return redirect(url_for('forgotPass'))
    
    return render_template("forgotPass.html")

@app.route('/resetPass/<token>', methods=['GET', 'POST'])
def resetPass(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)  # Token is valid for 1 hour
    except (SignatureExpired, BadTimeSignature):
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgotPass'))

    if request.method == 'POST':
        password = sanitize_input(request.form.get('password'), input_type='password')
        confirm_password = sanitize_input(request.form.get('confirm_password'), input_type='password')

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'warning')
            return render_template('resetPass.html', token=token)

        conn = sqlite3.connect("../database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE email = ?", (email,))
        user_row = cursor.fetchone()

        if user_row:
            hashed_password = ph.hash(password)
            cursor.execute("UPDATE Users SET password = ? WHERE email = ?", (hashed_password, email))
            conn.commit()
            flash('Your password has been updated!', 'success')
            print("Your password has been updated. ")
        else:
            flash('An error occurred. Please try again.', 'danger')
        conn.close()

        return redirect(url_for('login'))

    return render_template('resetPass.html', token=token)


@app.route("/logout")
def logout():
    # Clear the user's session
    session.clear()
    
    # Redirect to the login page or home page after logout
    return redirect(url_for("login"))

# Strong Password complexity 
def passwordStrength(password):
    # At least 12 characters long, contains at least one digit, one uppercase letter, one lowercase letter, and one special character
    pattern = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,128}$")
    # return pattern.match(password)
    match = pattern.match(password)
    print(f"Password: {password}, Match: {match}")
    return match

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def register():
    if request.method == "POST":
        name = sanitize_input(request.form.get("name"))
        password = sanitize_input(request.form.get("password"), input_type='password')
        phone_number = sanitize_input(request.form.get("phoneNum"))
        email = sanitize_input(request.form.get("email"), input_type='email')
        role = "user"

        if not passwordStrength(password):
            flash("Password must be at least 8 characters long, contain at least one digit, one uppercase letter, one lowercase letter, and one special character.", "error")
            return redirect(url_for("register"))

        hashed_password = ph.hash(password)

        conn = sqlite3.connect("../database.db")
        cursor = conn.cursor()
        try:
            print("success")
            cursor.execute(
                """INSERT INTO Users (name, password, phoneNum, email, role, created_at,login_attempts, is_verified) 
                   VALUES (?, ?, ?, ?, ?, datetime('now'), 0 , 0)""",
                (name, hashed_password, phone_number, email, role)
            )
            conn.commit()
            app.logger.info("Cursor about to commit this %s", cursor)

            # Send a account confirmation email
            token = serializer.dumps(email,salt='test')
            # token = serializer.dumps(email, salt='password-reset-salt')
            verification_url = url_for('verifyAccount', token=token, _external=True)
            subject = 'Complete Your Registration'
            body = f'''You're Almost There! \n Click On The Link To Complete Your Account Creation.\n
                        {verification_url}
                        If You Did Not Make This Request, Simply Ignore This Email and No Changes Will Be Made.
                        '''
            send_email(email, subject, body)
            flash("Your account has been successfully created!", "success")
            print("success")
            app.logger.info("Sent an Registration Email to %s", email)
            return redirect(url_for("login"))

        except sqlite3.IntegrityError as e:
            app.logger.error("Damn this broke %s", e)
            conn.rollback()
            if "UNIQUE constraint failed: Users.email" in str(e):
                flash("An account with this email already exists. Please try a different email.", "error")
                print("IntegrityError: An account with this email already exists.")
            else:
                flash("An error has occurred during registration. Please try again later.", "error")
                print("Error:", e)
        
        except Exception as e:
            conn.rollback()
            flash("An error has occurred during registration. Please try again later.", "error")
            print("Error:", e)
            app.logger.error("Following error occured! %s", e)
        
        finally:
            conn.close()

        return redirect(url_for("register"))
    else:
        return render_template("register.html")


@app.route("/verifyAccount/", methods=["GET","POST"])
def verifyAccount():
    token = request.args.get('token')
    try:
        email = serializer.loads(token, salt='test',max_age=86400)
    except Exception as e:
        print(e)
    
    conn = sqlite3.connect("../database.db")
    cursor = conn.cursor()
    try: 
        cursor.execute(
                    "UPDATE Users SET is_verified = 1 WHERE  email = ?",
                    (email,)
                )
        conn.commit()
    except:
        print("dB Transaction failed. User account still unverified.")
    flash("Your account has been verified successfully! Please Login.")
    return redirect(url_for('login'))
#HERE

# try:
#         email = serializer.loads(token, salt='password-reset-salt', max_age=3600)  # Token is valid for 1 hour
# except (SignatureExpired, BadTimeSignature):
#         flash('The reset link is invalid or has expired.', 'danger')
#         return redirect(url_for('forgotPass'))
#     serializer.load(``)

def save_image_to_database(image):
    if image:
        try:
            image_blob = image.read()
            return image_blob
        except Exception as e:
            print("Error reading image:", e)
            return None
    else:
        return None


@app.route("/upload_product", methods=["GET", "POST"])
@otp_required
def upload_product():

    if request.method == "POST":

        if "user_id" in session:
            user_id = session["user_id"]
        else:
            flash("User not logged in. Please log in to upload a product.", "error")
            return redirect(url_for("login"))
            
        product_name = sanitize_input(request.form["product_name"])
        description = sanitize_input(request.form["description"])
        price = sanitize_input(request.form["price"])
        size = sanitize_input(request.form["size"])
        condition = sanitize_input(request.form["condition"])
        quantity = sanitize_input(request.form["quantity"])

        image = request.files["image"]
        image_blob = save_image_to_database(image)

        # Print the values to check if they are correct
        print(f"User ID: {user_id}")
        print(f"Product Name: {product_name}")
        print(f"Description: {description}")
        print(f"Price: {price}")
        print(f"Size: {size}")
        print(f"Condition: {condition}")
        print(f"Quantity: {quantity}")

        # Connect to the database
        conn = sqlite3.connect("../database.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                """ INSERT INTO Products (user_id, product_name, description, price, size, condition, image_blob, quantity, created_at,
                verified) VALUES  (? ,?, ?, ?, ?, ?, ?, ?, datetime('now'),0)""",
                (
                    user_id,
                    product_name,
                    description,
                    price,
                    size,
                    condition,
                    image_blob,
                    quantity,
                ),
            )
            conn.commit()
            conn.close()
            flash("Your product has been successfully uploaded!", "Success")
            return redirect(url_for("user_home"))

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

@app.route("/product_image/<int:product_id>")
def product_image(product_id):
    # Connect to the database
    conn = sqlite3.connect("../database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT image_blob FROM Products WHERE product_id = ?", (product_id,))
    image_blob = cursor.fetchone()[0]
    conn.close()

    # Convert BLOB back to image
    response = make_response(image_blob)
    response.headers.set('Content-Type', 'image/jpeg')
    response.headers.set(
        'Content-Disposition', 'attachment', filename=f'product_{product_id}.jpg')
    return response

# Route to form used to add a new user to the database
# @app.route("/enternew")
# def enternew():
#     if "name" in session and session.get("role") == "admin":
#         return render_template("user.html", name=session["name"])
#     else:
#         return redirect(url_for("login"))


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
            with sqlite3.connect("../database.db") as con:
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
    con = sqlite3.connect("../database.db")
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
            con = sqlite3.connect("../database.db")
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
            current_user = session["name"]
            # Use the hidden input value of id from the form to get the user_id
            user_id = request.form["user_id"]
            name = request.form["name"]
            password = request.form["password"]
            phoneNum = request.form["phoneNum"]
            email = request.form["email"]
            role = request.form["role"]

            # UPDATE a specific record in the database based on the user_id
            with sqlite3.connect("../database.db") as con:
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
            create_log(
                event_type="Update",
                user_id=current_user,
                details=current_user + " edited data of " + name,
            )
            # Send the transaction message to result.html
            return render_template("result.html", msg=msg)


# Route used to DELETE a specific record in the database
@app.route("/delete", methods=["POST", "GET"])
def delete():
    if request.method == "POST":
        try:
            current_user = session["user_id"]
            # Use the hidden input value of id from the form to get the user_id
            user_id = request.form["user_id"]
            name = request.form["name"]
            # Connect to the database and DELETE a specific record based on user_id
            with sqlite3.connect("../database.db") as con:
                cur = con.cursor()
                cur.execute("DELETE FROM Users WHERE user_id = ?", (user_id,))
                con.commit()
                msg = "Record successfully deleted from the database"
        except Exception as e:
            con.rollback()
            msg = "Error in the DELETE: " + str(e)

        finally:
            con.close()
            create_log(
                event_type="Delete",
                user_id=current_user,
                details=session["name"] + " deteled profile of " + name,
            )
            # Send the transaction message to result.html
            return render_template("result.html", msg=msg)


# Route View all products
@app.route("/view_products")
@otp_required
def view_products():

    if "user_id" in session:
        user_id = session["user_id"]

    conn = sqlite3.connect("../database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT product_id, product_name, price, image_blob, verified FROM Products"
    )
    products = cursor.fetchall()
    conn.close()

    # Converting the fetched data into a list of dictionaries
    products_list = []
    for product in products:
        product_dict = {
            "product_id": product[0],
            "product_name": product[1],
            "price": product[2],
            "image_blob": product[3],
            "verified": product[4],
        }
        products_list.append(product_dict)

    return render_template(
        "view_products.html", products_list=products_list, user_id=user_id
    )

@app.route("/search_products", methods=["GET"])
@limiter.limit("20 per minute") 
def search_products():
    query = sanitize_input(request.args.get("query"))
    if not query:
        return redirect(
            url_for("view_products")
        )  # Redirect to products page if no query is provided

    conn = sqlite3.connect("../database.db")
    conn.row_factory = sqlite3.Row  # This will let us access rows as dictionaries
    cursor = conn.cursor()

    # Search for products that match the query
    cursor.execute(
        """SELECT * FROM Products WHERE product_name LIKE ? OR description LIKE ?""",
        ("%" + query + "%", "%" + query + "%"),
    )
    products_list = cursor.fetchall()
    conn.close()

    return render_template("view_products.html", products_list=products_list)


@app.route("/product_details/<int:product_id>")
def product_details(product_id):

    if "user_id" in session:
        user_id = session["user_id"]

    conn = sqlite3.connect("../database.db")
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
            "image_blob": product_details[7],
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
    conn = sqlite3.connect("../database.db")
    cursor = conn.cursor()
    # Fetch reviews
    cursor.execute(
        """SELECT r.review_id, r.rating, r.comment, r.created_at, u.name 
                          FROM Reviews r JOIN Users u ON r.user_id = u.user_id 
                          WHERE r.product_id = ? ORDER BY r.created_at DESC""",
        (product_id,),
    )
    reviews = cursor.fetchall()
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
@otp_required
def my_products():

    if "user_id" in session:
        user_id = session["user_id"]

    conn = sqlite3.connect("../database.db")
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
            "image_blob": product[7],
        }
        products_list.append(product_dict)

    return render_template(
        "my_products.html", products_list=products_list, user_id=user_id
    )


@app.route("/my_products_details/<int:product_id>")
def my_products_details(product_id):
    user_id = session.get("user_id")
    review_list = my_products_reviews(product_id)
    conn = sqlite3.connect("../database.db")
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
            "image_blob": product_details[7],
            "quantity": product_details[8],
            "created_at": product_details[9],
            "verified": product_details[10],
        }

    conn.close()
    # print(product_details, file=sys.stderr)
    # print(review_list, file=sys.stderr)

    return render_template(
        "my_products_details.html",
        product=product_dict,
        reviews=review_list,
        user_id=user_id,
        product_id=product_id,
    )


def my_products_reviews(product_id):
    user_id = session.get("user_id")
    conn = sqlite3.connect("../database.db")
    cursor = conn.cursor()
    # Fetch reviews
    cursor.execute(
        """SELECT r.review_id, r.rating, r.comment, r.created_at, u.name 
                          FROM Reviews r JOIN Users u ON r.user_id = u.user_id 
                          WHERE r.product_id = ? ORDER BY r.created_at DESC""",
        (product_id,),
    )
    reviews = cursor.fetchall()
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

    conn = sqlite3.connect("../database.db")
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

    user_id = sanitize_input(str(session["user_id"]))
    rating = sanitize_input(request.form["rating"])
    comment = sanitize_input(request.form["comment"])
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("../database.db")
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

    conn = sqlite3.connect("../database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM Products WHERE product_id = ? ",
        (product_id,),
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
        conn = sqlite3.connect("../database.db")
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
    return redirect(url_for("view_products_admin", product_id=product_id))


@app.route("/view_cart")
def view_cart():
    user_id = session.get("user_id")
    db_path = DATABASE_PATH


    if not user_id:
        return redirect(url_for("login"))  # Redirect to login if user is not logged in

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """SELECT c.cart_item_id, p.product_name, p.price, c.quantity 
                      FROM Cart_Items c 
                      JOIN Products p ON c.product_id = p.product_id 
                      JOIN Shopping_Cart s ON c.cart_id = s.cart_id 
                      WHERE s.user_id = ?""",
        (user_id,),
    )
    cart_items = cursor.fetchall()

    cursor.execute(
        """SELECT SUM(p.price * c.quantity)
                      FROM Cart_Items c 
                      JOIN Products p ON c.product_id = p.product_id 
                      JOIN Shopping_Cart s ON c.cart_id = s.cart_id 
                      WHERE s.user_id = ?""",
        (user_id,),
    )
    total_amount = cursor.fetchone()[0] or 0.00

    conn.close()

    return render_template(
        "view_cart.html", cart_items=cart_items, total_amount=total_amount
    )


@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    user_id = session.get("user_id")
    product_id = request.form.get("product_id")
    quantity = int(request.form.get("quantity", 1))  # Default quantity to 1 if not provided

    if not user_id:
        return redirect(url_for("login"))  # Redirect to login if user is not logged in

    db_path = DATABASE_PATH

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if a cart exists for this user
        cursor.execute("SELECT cart_id FROM Shopping_Cart WHERE user_id = ?", (user_id,))
        cart = cursor.fetchone()

        if cart:
            cart_id = cart[0]
        else:
            # Create a new cart for the user if it doesn't exist
            cursor.execute("INSERT INTO Shopping_Cart (user_id) VALUES (?)", (user_id,))
            cart_id = cursor.lastrowid

        # Check if the product is already in the cart
        cursor.execute(
            "SELECT quantity FROM Cart_Items WHERE cart_id = ? AND product_id = ?",
            (cart_id, product_id),
        )
        cart_item = cursor.fetchone()

        if cart_item:
            # Update the quantity if the product is already in the cart
            new_quantity = cart_item[0] + quantity
            cursor.execute(
                "UPDATE Cart_Items SET quantity = ? WHERE cart_id = ? AND product_id = ?",
                (new_quantity, cart_id, product_id),
            )
        else:
            # Add the product to the cart if it is not already there
            cursor.execute(
                "INSERT INTO Cart_Items (cart_id, product_id, quantity) VALUES (?, ?, ?)",
                (cart_id, product_id, quantity),
            )

        conn.commit()
    except sqlite3.Error as e:
        return f"An error occurred: {e}", 500
    finally:
        conn.close()

    return redirect(url_for("my_products_details", product_id=product_id))

@app.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    user_id = session.get("user_id")
    cart_item_id = request.form.get("cart_item_id")
    db_path = DATABASE_PATH


    if not user_id:
        return redirect(url_for("login"))  # Redirect to login if user is not logged in

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM Cart_Items WHERE cart_item_id = ? AND cart_id IN (SELECT cart_id FROM Shopping_Cart WHERE user_id = ?)",
        (cart_item_id, user_id),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("view_cart"))


@app.route("/update_cart", methods=["POST"])
def update_cart():
    user_id = session.get("user_id")
    cart_item_id = request.form.get("cart_item_id")
    quantity = int(request.form.get("quantity"))
    db_path = DATABASE_PATH


    if not user_id:
        return redirect(url_for("login"))  # Redirect to login if user is not logged in

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE Cart_Items SET quantity = ? WHERE cart_item_id = ? AND cart_id IN (SELECT cart_id FROM Shopping_Cart WHERE user_id = ?)",
        (quantity, cart_item_id, user_id),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("view_cart"))


@app.route("/proceed_to_payment", methods=["GET", "POST"])
def proceed_to_payment():
    user_id = session.get("user_id")
    db_path = DATABASE_PATH

    if not user_id:
        return redirect(url_for("login"))  # Redirect to login if user is not logged in

    # Fetch the cart items and total amount
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT c.cart_item_id, p.product_name, p.price, c.quantity 
                      FROM Cart_Items c 
                      JOIN Products p ON c.product_id = p.product_id 
                      JOIN Shopping_Cart s ON c.cart_id = s.cart_id 
                      WHERE s.user_id = ?""",
        (user_id,),
    )
    cart_items = cursor.fetchall()

    cursor.execute(
        """SELECT SUM(p.price * c.quantity)
                      FROM Cart_Items c 
                      JOIN Products p ON c.product_id = p.product_id 
                      JOIN Shopping_Cart s ON c.cart_id = s.cart_id 
                      WHERE s.user_id = ?""",
        (user_id,),
    )
    total_amount = cursor.fetchone()[0] or 0.00
    conn.close()

    return render_template(
        "payment_form.html", total_amount=total_amount, cart_items=cart_items
    )


@app.route("/process_payment", methods=["POST"])
def process_payment():
    db_path = DATABASE_PATH
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))  # Redirect to login if user is not logged in

    shipping_address = sanitize_input(request.form["shipping_address"])
    payment_method = sanitize_input(request.form["payment_method"])
    total_amount = sanitize_input(request.form["total_amount"])
    order_date = datetime.now()
    status = "Pending"  # Initial status of the order
    tracking_num = ""  # Initially empty, will be updated when the order is shipped

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")

        # Insert into Orders table
        cursor.execute(
            """INSERT INTO Orders (user_id, order_date, total_amount, status, tracking_num, shipping_address, created_at)
                          VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                order_date,
                total_amount,
                status,
                tracking_num,
                shipping_address,
                order_date,
            ),
        )
        order_id = cursor.lastrowid

        # Fetch cart items
        cursor.execute(
            """SELECT c.product_id, c.quantity, p.price 
                          FROM Cart_Items c 
                          JOIN Products p ON c.product_id = p.product_id 
                          JOIN Shopping_Cart s ON c.cart_id = s.cart_id 
                          WHERE s.user_id = ?""",
            (user_id,),
        )
        cart_items = cursor.fetchall()

        # Insert into Order_Items table
        for item in cart_items:
            product_id, quantity, price = item
            cursor.execute(
                """INSERT INTO Order_Items (order_id, product_id, quantity, price)
                              VALUES (?, ?, ?, ?)""",
                (order_id, product_id, quantity, price),
            )

            # Update product quantity
            cursor.execute(
                """UPDATE Products SET quantity = quantity - ? WHERE product_id = ?""",
                (quantity, product_id),
            )

        # Insert into Payments table
        payment_date = order_date
        cursor.execute(
            """INSERT INTO Payments (order_id, payment_amt, payment_method, payment_date, status)
                          VALUES (?, ?, ?, ?, ?)""",
            (order_id, total_amount, payment_method, payment_date, status),
        )

        # Clear the cart
        cursor.execute(
            """DELETE FROM Cart_Items WHERE cart_id IN 
                          (SELECT cart_id FROM Shopping_Cart WHERE user_id = ?)""",
            (user_id,),
        )

        conn.commit()
        flash("Payment successful!", "success")
        return render_template("success.html")

    except Exception as e:
        # Rollback the transaction if there's any error
        conn.rollback()
        return jsonify({"error": str(e)})

    finally:
        conn.close()


@app.route("/view_products_admin")
def view_products_admin():
    # Connect to the SQLite3 datatabase and
    # SELECT rowid and all Rows from the users table.
    con = sqlite3.connect("../database.db")
    con.row_factory = sqlite3.Row

    cur = con.cursor()
    cur.execute("SELECT * FROM Products")

    rows = cur.fetchall()
    con.close()
    # Send the results of the SELECT to the list.html page
    return render_template("view_products_admin.html", rows=rows)


def create_log(event_type, user_id=None, details=None):
    conn = sqlite3.connect("../database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO logs (event_type, user_id, details) VALUES (?, ?, ?)",
        (event_type, user_id, details),
    )
    conn.commit()
    conn.close()


@app.route("/logs")
def logs():
    # Connect to the SQLite3 datatabase and
    # SELECT rowid and all Rows from the users table.
    con = sqlite3.connect("../database.db")
    con.row_factory = sqlite3.Row

    cur = con.cursor()
    cur.execute("SELECT * FROM Logs")

    rows = cur.fetchall()
    con.close()
    # Send the results of the SELECT to the list.html page
    return render_template("logs.html", rows=rows)


if __name__ == "__main__":
    with app.app_context():
        try:
            app.config['SESSION_SQLALCHEMY'].create_all()  # Create the sessions table
        except Exception as e:
            print(f"Error creating database: {e}")
    Session(app)

    
    app.run(debug=True,use_reloader = False)

    # app.run(debug=True)
#     handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
#     handler.setLevel(logging.INFO)
#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     handler.setFormatter(formatter)
#     app.logger.addHandler(handler)
#     app.logger.info("Hello worls")