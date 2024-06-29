import os
from flask import Flask, flash, redirect, render_template, request, session, url_for
import sqlite3
from datetime import datetime, timedelta, timezone
from matplotlib import use
# from numpy import product # what is this for ah?
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

app = Flask(__name__)

def sanitize_input(input_data, input_type="text"):
    if input_type == "text":
        return re.sub(r"[^\w\s]", "", input_data)
    elif input_type == "email":
        return re.sub(r"[^\w\s@.-]", "", input_data)
    elif input_type == "password":
        # Passwords should be hashed and salted, but if you want to allow special characters, sanitize differently
        return re.sub(r"[^\w\s@#$%^&*()_+=-]", "", input_data)
    elif input_type == "phone":
        return re.sub(r"[^\d]", "", input_data)
    return input_data

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        name = sanitize_input(request.form.get("name"))
        password = sanitize_input(request.form.get("password"))
        # hashed_password = generate_password_hash(password)
        phone_number = sanitize_input(request.form.get("phoneNum"))
        email = sanitize_input(request.form.get("email"))
        role = sanitize_input(request.form.get("role"))

        hashed_password = ph.hash(password)
        print(f"hashed_password: {hashed_password}")
        
        # Connect to the database
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                """ INSERT INTO Users (name, password, phoneNum, email, role, created_at) VALUES  (?, ?, ?, ?, ?, datetime('now'))""",
                (
                    name,
                    hashed_password,
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