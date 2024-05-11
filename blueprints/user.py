from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from modules.database import *
from datetime import datetime

user = Blueprint("user", __name__, static_folder="static", template_folder="templates")

# Define a home route
@user.route("/")
def home():
    if "user" in session:
        role = session["user"]
        print("You are logged in as", role)
        return render_template("index.html")
    else:
        return redirect(url_for("login"))


@user.route("/payment", methods=["POST"])
def payment():
    if not ("accountId" and "accountRole" in session):
        return redirect(url_for("login"))
    try:
        # Connect to the database
        db = get_sqlite_database()
        cursor = db.cursor()

        # Extract details from the POST request or form
        studio = request.form.get("studio")
        cursor.execute(
            """
            SELECT studioName 
            FROM Studio  
            WHERE studioId = ?
        """,
            (studio,),
        )
        studioName = cursor.fetchone()[0]
        date = request.form.get("date")
        time = request.form.get("time")
        tickets = int(request.form.get("tickets"))
        price = float(request.form.get("price"))
        screeningId = request.form.get("screeningId")
        filmid = request.form.get("filmid")
        filmName = request.form.get("filmName")

        return render_template(
            "payment.html",
            studioId=studio,
            studioName=studioName,
            date=date,
            time=time,
            tickets=tickets,
            screeningId=screeningId,
            filmid=filmid,
            filmName=filmName,
            price=price,
        )

    except Exception as e:
        print(f"An error occurred: {e}")


@user.route("/process_payment", methods=["POST"])
def process_payment():
    try:
        # Connect to the database
        db = get_sqlite_database()
        cursor = db.cursor()

        current_user_id = None
        if "accountId" in session:
            current_user_id = session["accountId"]

        cardtype = request.form.get("card-type")
        screeningid = request.form.get("screeningId")
        tickets = request.form["tickets"]
        price = request.form.get("price")
        filmName = request.form.get("filmName")

        # Get current timestamp
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Begin a transaction
        cursor.execute("BEGIN TRANSACTION")

        # Check if there are available slots
        cursor.execute(
            "SELECT screeningCapacity FROM Screening WHERE screeningId = ?",
            (screeningid,),
        )
        screening_capacity = cursor.fetchone()
        screeningCapacity = screening_capacity[0]
        # return render_template("success.html")

        if screeningCapacity >= int(tickets):
            # There are enough slots available, proceed with booking
            cursor.execute(
                "INSERT INTO Transactions (transactionsAmount, transactionsTimestamp, transactionsPaymentMethod) VALUES (?, ?, ?)",
                (price, current_timestamp, cardtype),
            )
            transactions_id = cursor.lastrowid

            cursor.execute(
                "INSERT INTO Booking (userid, filmName, bookingDate, bookingTime, transactionsId, bookingStatus, numberOfTickets) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    current_user_id,
                    filmName,
                    current_timestamp.split()[0],
                    current_timestamp.split()[1],
                    transactions_id,
                    "confirmed",
                    tickets,
                ),
            )

            # Decrement available slots
            # cursor.execute("UPDATE Screening SET screeningCapacity = screeningCapacity - ? WHERE screeningId = 9", (int(tickets),))
            cursor.execute(
                "UPDATE Screening SET screeningCapacity = screeningCapacity - ? WHERE screeningId = ?",
                (tickets, screeningid),
            )

            # Commit the transaction
            cursor.execute("COMMIT")
            db.close()

            flash("Payment successful!", "success")
            return render_template("success.html")
        else:
            # Not enough slots available, rollback the transaction
            cursor.execute("ROLLBACK")
            db.close()

            flash(
                "Sorry, there are not enough slots available for your booking.", "error"
            )
            return render_template("error.html")

    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
        # Handle the error appropriately (e.g., show an error message to the user)


@user.route("/moviereviews/<int:filmid>", methods=["GET", "POST"])
def moviereviews(filmid):
    # Ensure user is logged in
    if not ("accountId" and "accountRole" in session):
        return redirect(url_for("login"))

    user_id = session["accountId"]
    try:
        # Connect to the database
        db = get_sqlite_database()
        cursor = db.cursor()

        # If it"s a POST request, save/update the review
        if request.method == "POST":
            rating = request.form.get("rating")
            review = request.form.get("review")
            review_title = request.form.get("reviewTitle")

            # Check if review already exists
            cursor.execute(
                """SELECT * FROM Film_Review WHERE userId = ? AND filmId = ?""",
                (user_id, filmid),
            )
            existing_review = cursor.fetchone()

            cursor.execute(
                "SELECT STRFTIME('%Y-%m-%d %H:%M:%S', DATETIME('now', 'localtime'))"
            )
            date = cursor.fetchone()[0]
            date = str(date)
            if existing_review:
                # Update the existing review
                cursor.execute(
                    """UPDATE Film_Review SET filmReviewTitle = ?, filmReviewRating = ?, filmReviewDescription = ?, filmReviewDate = ? WHERE userId = ? AND filmId = ?""",
                    (review_title, rating, review, date, user_id, filmid),
                )
            else:
                # Insert new review
                cursor.execute(
                    """INSERT INTO Film_Review (filmReviewTitle, filmReviewRating, filmReviewDescription, filmReviewDate, userId, filmId) VALUES (?, ?, ?, ?, ?, ?)""",
                    (review_title, rating, review, date, user_id, filmid),
                )

            db.commit()
            referrer = request.form.get("referrer")
            return redirect(referrer or url_for("moviebooking", filmid=filmid))

        # If it"s a GET request, fetch the existing review (if any) to display
        cursor.execute(
            "SELECT filmReviewTitle, filmReviewRating, filmReviewDescription, filmReviewDate FROM Film_Review WHERE userId = ? AND filmId = ?",
            (user_id, filmid),
        )
        review_data = cursor.fetchone()
        existing_review_title = review_data[0] if review_data else ""
        existing_rating = review_data[1] if review_data else ""
        existing_review = review_data[2] if review_data else ""
        existing_review_date = review_data[3] if review_data else ""
        # Fetch the movie title for display
        cursor.execute("""SELECT filmName FROM Film WHERE filmId = ?""", (filmid,))
        film_name = cursor.fetchone()[0]

        return render_template(
            "moviereviews.html",
            existing_review_title=existing_review_title,
            filmid=filmid,
            film_name=film_name,
            existing_review=existing_review,
            existing_rating=existing_rating,
            existing_review_date=existing_review_date,
        )

    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")


@user.route("/remove_review", methods=["POST"])
def remove_review():
    if not ("accountId" and "accountRole" in session):
        return redirect(url_for("login"))
    try:
        review_id = request.form.get("review_id")  # Get review_id from the form
        source = request.form.get("source")
        if source == "moviebooking":
            filmid = request.form.get("filmid")
        if not review_id:
            return "Review ID is missing", 400

        # Convert review_id to int
        review_id = int(review_id)

        # Connect to the database
        db = get_sqlite_database()
        cursor = db.cursor()

        # Delete the review with the given review_id
        cursor.execute(
            """
            DELETE FROM Film_Review 
            WHERE FilmReviewId = ?
        """,
            (review_id,),
        )

        db.commit()
        if source == "moviebooking":
            return redirect(url_for("moviebooking", filmid=filmid))
        return redirect(url_for("profile") + "#reviews")

    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
