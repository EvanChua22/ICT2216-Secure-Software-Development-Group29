from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from modules.database import *
import base64

filmmaker = Blueprint(
    "filmmaker", __name__, static_folder="static", template_folder="templates"
)


class DuplicateFilmError(Exception):
    pass


class OngoingScreeningError(Exception):
    pass


class DuplicateScreeningError(Exception):
    pass


# Define the filmmaker dashboard route
@filmmaker.route("/")
def dashboard():
    if "accountId" and "accountRole" in session:
        id = session["accountId"]
        role = session["accountRole"]
        print("You are logged in as " + role + " with the ID of " + str(id))

        # Get SQLite Database Connection and its cursor
        sqlDb = get_sqlite_database()
        sqlCursor = sqlDb.cursor()

        # Get MongoDB Database Connection
        noSqlDb = get_mongodb_database()

        if request.method == "GET":
            # get the respective data for the various charts from MongoDB
            (
                genresList,
                countriesList,
                companiesList,
                boxOfficeList,
                runTimeList,
                budgetList,
            ) = getChartData(noSqlDb)

            # Retrieve the list of movies owned by the particular filmmaker based on their ID from SQLite
            films_list = getAllFilmsOwned(id, sqlCursor)

            # Retrieve the list of studios from SQLite
            studios = getAllStudios(sqlCursor)

            # Retrieve the list of department from MongoDB
            departmentList = getAllDepartments(noSqlDb)

            return render_template(
                "dashboard.html",
                genresData=genresList,
                countryData=countriesList,
                companiesData=companiesList,
                boxOfficeData=boxOfficeList,
                runtimeData=runTimeList,
                budgetData=budgetList,
                studios=studios,
                films_list=films_list,
                department=departmentList,
            )

    else:
        return redirect(url_for("login"))


# Define filmmaker create film route
@filmmaker.route("/createfilm", methods=["GET", "POST"])
def createFilm():
    if "accountId" and "accountRole" in session:
        id = session["accountId"]
        role = session["accountRole"]
        print("You are logged in as " + role + " with the ID of " + str(id))

        # Get SQLite Database Connection and its cursor
        sqlDb = get_sqlite_database()
        sqlCursor = sqlDb.cursor()

        # Get MongoDB Database Connection
        noSqlDb = get_mongodb_database()

        if request.method == "POST":
            # Insert film into SQLite according to the filmmaker based on their ID
            createFilm(id, sqlDb, sqlCursor)

            return redirect(url_for("filmmaker.dashboard"))

        elif request.method == "GET":
            # Retrieve the list of studios from SQLite
            studios = getAllStudios(sqlCursor)
            casts = getAllCasts(noSqlDb)

            return render_template("createfilm.html", studios=studios, casts=casts)

    else:
        return redirect(url_for("login"))


# Define filmmaker edit film route
@filmmaker.route("/editfilm/<int:filmId>", methods=["GET", "POST"])
def editFilm(filmId):
    if "accountId" and "accountRole" in session:
        id = session["accountId"]
        role = session["accountRole"]
        print("You are logged in as " + role + " with the ID of " + str(id))

        # Get SQLite Database Connection and its cursor
        sqlDb = get_sqlite_database()
        sqlCursor = sqlDb.cursor()

        # Get MongoDB Database Connection
        noSqlDb = get_mongodb_database()

        if request.method == "POST":
            button_clicked = request.form["button"]

            # Update the film and film screening based on filmId
            if button_clicked == "update":
                updateFilm(filmId, sqlDb, sqlCursor)
                createFilmScreening(filmId, sqlDb, sqlCursor)

            # Delete the film based on the filmId
            elif button_clicked == "delete":
                deleteFilm(filmId, sqlDb, sqlCursor)

            return redirect(url_for("filmmaker.dashboard"))

        elif request.method == "GET":
            # Retrieve the film data based on the filmId from SQLite
            (
                film_name,
                film_casts,
                film_poster,
                film_synopsis,
                film_runtime,
                film_release_date,
                film_maturity_rating,
                film_genre,
                film_language,
                film_screenings_list,
            ) = getFilmById(filmId, sqlDb, sqlCursor)

            # Retrieve the list of studios from SQLite
            studios = getAllStudios(sqlCursor)

            # Retrieve the list of casts from MongoDB
            casts = getAllCasts(noSqlDb)

            return render_template(
                "editfilm.html",
                film_name=film_name,
                film_casts=film_casts,
                film_poster=film_poster,
                film_synopsis=film_synopsis,
                film_runtime=film_runtime,
                film_release_date=film_release_date,
                film_maturity_rating=film_maturity_rating,
                film_genre=film_genre,
                film_language=film_language,
                film_screenings=film_screenings_list,
                studios=studios,
                casts=casts,
            )

    else:
        return redirect(url_for("login"))


# Define filmmaker create studio route
@filmmaker.route("/createstudio", methods=["GET", "POST"])
def createStudio():
    if "accountId" and "accountRole" in session:
        id = session["accountId"]
        role = session["accountRole"]
        print("You are logged in as " + role + " with the ID of " + str(id))

        # Get SQLite Database Connection and its cursor
        sqlDb = get_sqlite_database()
        sqlCursor = sqlDb.cursor()

        if request.method == "POST":
            # Create a new studio in SQLite
            createStudio(sqlDb, sqlCursor)

            return redirect(url_for("filmmaker.dashboard"))

        elif request.method == "GET":
            return render_template("createstudio.html")

    else:
        return redirect(url_for("login"))


# Define filmmaker edit studio route
@filmmaker.route("/editstudio/<int:studioId>", methods=["GET", "POST"])
def editStudio(studioId):
    if "accountId" and "accountRole" in session:
        id = session["accountId"]
        role = session["accountRole"]
        print("You are logged in as " + role + " with the ID of " + str(id))

        # Get SQLite Database Connection and its cursor
        sqlDb = get_sqlite_database()
        sqlCursor = sqlDb.cursor()

        if request.method == "POST":
            # Update Studio
            updateStudio(studioId, sqlDb, sqlCursor)

            return redirect(url_for("filmmaker.dashboard"))

        elif request.method == "GET":
            # Get studio name and studio address
            studio_name, studio_address = getStudioById(studioId, sqlCursor)

            return render_template(
                "editStudio.html",
                studio_name=studio_name,
                studio_address=studio_address,
            )

    else:
        return redirect(url_for("login"))


# Define filmmaker search crew route
@filmmaker.route("/searchcrew")
def searchCrew():
    name = request.args.get("name")
    job = request.args.get("job")
    department = request.args.get("department")

    if name or department and job:
        mongodb = get_mongodb_database()
        collection = mongodb["crew"]

        d = (
            collection.find(
                {
                    "$or": [
                        {"name": {"$regex": f"^{name}"}},
                    ],
                    "department": department,
                    "job": job,
                }
            )
            .limit(50)
            .explain()
        )

        print("Execution: ", d["executionStats"])

        results = list(
            collection.find(
                {
                    "$or": [
                        {"name": {"$regex": f"^{name}"}},
                    ],
                    "department": department,
                    "job": job,
                }
            ).limit(50)
        )

    return render_template("search_crew_results.html", results=results)


# Define filmmaker get job route
@filmmaker.route("/getjob")
def getJob():
    selected_department = request.args.get("department")

    if selected_department:
        mongodb = get_mongodb_database()
        collection = mongodb["crew"]

        results = collection.aggregate(
            [
                {"$match": {"department": selected_department}},
                {"$group": {"_id": "$job"}},
                {"$project": {"_id": 0, "unique_jobs": "$_id"}},
            ]
        )

        e = []
        for doc in results:
            e.append(doc["unique_jobs"])

        return render_template("joboption.html", results=e)


# Film CRUD
def createFilm(filmmakerId, db, cursor):
    filmmaker_id = filmmakerId
    movie_name = request.form.get("movie_name")
    movie_synopsis = request.form.get("movie_synopsis")
    movie_release_date = request.form.get("movie_release_date")
    movie_cast = request.form.getlist("cast-select[]")
    movie_poster = request.files["movie_poster"]
    movie_genre = request.form.get("movie_genre")
    movie_language = request.form.get("movie_language")
    movie_rating = request.form.get("movie_rating")
    movie_duration = request.form.get("movie_duration")

    movie_cast = ", ".join(movie_cast)

    poster_binary_data = None

    try:
        cursor.execute("SELECT filmName FROM Film WHERE filmName = ?", (movie_name,))

        if cursor.fetchone():
            raise DuplicateFilmError("Duplicate film found")

        if movie_poster.filename != "":
            poster_binary_data = movie_poster.read()
        # Insert user data into the database

        cursor.execute(
            "INSERT INTO Film (filmName, filmSynopsis, filmReleaseDate, filmRunTime, filmCast, filmPoster, filmMaturityRating, filmLanguage, filmGenre, filmMakerId)"
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                movie_name,
                movie_synopsis,
                movie_release_date,
                movie_duration,
                movie_cast,
                poster_binary_data,
                movie_rating,
                movie_language,
                movie_genre,
                filmmaker_id,
            ),
        )

        inserted_film_id = cursor.lastrowid

        db.commit()
        flash("Film successfully created!", "success")
        print("success")

        createFilmScreening(inserted_film_id, db, cursor)
    except DuplicateFilmError as e:
        # Handle the custom exception
        db.rollback()
        flash("Error: Duplicate film found. Please try again.", "error")
        print("Error:", e)


def updateFilm(filmId, db, cursor):
    movie_name = request.form.get("movie_name")
    movie_synopsis = request.form.get("movie_synopsis")
    movie_release_date = request.form.get("movie_release_date")
    movie_cast = request.form.getlist("cast-select[]")
    movie_poster = request.files["movie_poster"]
    movie_genre = request.form.get("movie_genre")
    movie_language = request.form.get("movie_language")
    movie_rating = request.form.get("movie_rating")
    movie_duration = request.form.get("movie_duration")

    movie_cast = ", ".join(movie_cast)

    poster_binary_data = None

    try:
        cursor.execute(
            "SELECT filmName FROM Film WHERE filmName = ? AND filmId <> ?",
            (
                movie_name,
                filmId,
            ),
        )

        if cursor.fetchone():
            raise DuplicateFilmError("Duplicate film found")

        if movie_poster.filename != "":
            poster_binary_data = movie_poster.read()
            cursor.execute(
                "UPDATE Film SET filmName = ?, filmSynopsis = ?, filmReleaseDate = ?, filmRunTime = ?, "
                "filmCast = ?, filmPoster = ?, filmMaturityRating = ?, filmGenre = ?, filmLanguage = ? WHERE filmId = ?",
                (
                    movie_name,
                    movie_synopsis,
                    movie_release_date,
                    movie_duration,
                    movie_cast,
                    poster_binary_data,
                    movie_rating,
                    movie_genre,
                    movie_language,
                    filmId,
                ),
            )
        else:
            cursor.execute(
                "UPDATE Film SET filmName = ?, filmSynopsis = ?, filmReleaseDate = ?, filmRunTime = ?, "
                "filmCast = ?, filmMaturityRating = ?, filmGenre = ?, filmLanguage = ? WHERE filmId = ?",
                (
                    movie_name,
                    movie_synopsis,
                    movie_release_date,
                    movie_duration,
                    movie_cast,
                    movie_rating,
                    movie_genre,
                    movie_language,
                    filmId,
                ),
            )

        db.commit()
        flash("Film updated!", "success")
        print("film updated")

    except DuplicateFilmError as e:
        # Handle the custom exception
        db.rollback()
        flash("Error: Duplicate film found. Please try again.", "error")
        print("Error:", e)


def deleteFilm(filmId, db, cursor):
    try:
        cursor.execute(
            "SELECT screeningId FROM Screening WHERE filmId = ? and screeningStatus = ?",
            (filmId, "Waiting"),
        )
        if cursor.fetchone():
            raise OngoingScreeningError("Current film has ongoing screenings")

        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("DELETE FROM Film WHERE filmId = ?", (filmId,))
        db.commit()
        flash("Film deleted!", "success")
        print("film deleted")
    except OngoingScreeningError as e:
        db.rollback()
        flash(
            "Error: Film has ongoing screening. Wait until all screenings are finished",
            "error",
        )
        print("Error:", e)


def getFilmById(filmId, db, cursor):
    try:
        updateFilmScreeningStatus(filmId, db, cursor)

        cursor.execute(
            "SELECT filmName, filmCast, filmPoster, filmSynopsis, filmRunTime, filmReleaseDate, filmMaturityRating, filmGenre, filmLanguage FROM Film "
            "WHERE filmId = ?",
            (filmId,),
        )

        film_data = cursor.fetchone()

        (
            film_name,
            film_cast,
            film_poster_blob,
            film_synopsis,
            film_runtime,
            film_release_date,
            film_maturity_rating,
            film_genre,
            film_language,
        ) = film_data

        film_cast = film_cast.split(",")

        film_poster = base64.b64encode(film_poster_blob).decode("utf-8")

        cursor.execute(
            "SELECT S.screeningCapacity, S.screeningOriginalCapacity, ST.studioName, S.screeningDate, S.screeningTime, S.screeningPrice, S.screeningStatus "
            "FROM Screening S "
            "JOIN Studio ST ON S.studioId = ST.studioId "
            "WHERE s.filmId = ?",
            (filmId,),
        )

        film_screenings = cursor.fetchall()
        film_screenings_list = []

        for screening_data in film_screenings:
            (
                screening_capacity,
                screening_original_capacity,
                screening_studio,
                screening_date,
                screening_time,
                screening_price,
                screening_status,
            ) = screening_data
            screening_info = {
                "screening_capacity": screening_capacity,
                "screening_original_capacity": screening_original_capacity,
                "screening_studio": screening_studio,
                "screening_date": screening_date,
                "screening_time": screening_time,
                "screening_price": screening_price,
                "screening_status": screening_status,
            }
            film_screenings_list.append(screening_info)

        return (
            film_name,
            film_cast,
            film_poster,
            film_synopsis,
            film_runtime,
            film_release_date,
            film_maturity_rating,
            film_genre,
            film_language,
            film_screenings_list,
        )

    except Exception as e:
        # Handle the custom exception
        db.rollback()
        print("Error:", e)


def getAllFilmsOwned(filmmakerId, cursor):
    # get filmmaker data
    cursor.execute(
        "SELECT filmId, filmName, filmRunTime, filmPoster FROM Film WHERE filmmakerid = ?",
        (filmmakerId,),
    )
    films_data = cursor.fetchall()
    films_list = []

    for film_data in films_data:
        film_Id, film_name, film_runtime, film_poster_blob = film_data

        # Convert Blob to Base64 String
        film_poster_base64 = base64.b64encode(film_poster_blob).decode("utf-8")

        film_info = {
            "film_id": film_Id,
            "film_name": film_name,
            "film_runtime": film_runtime,
            "film_poster_base64": film_poster_base64,
        }
        films_list.append(film_info)

    return films_list


# Film Screening CRUD
def createFilmScreening(filmId, db, cursor):
    numRows = int(request.form.get("numRows"))

    if numRows == 0:
        return

    screening_studios_name = []
    screening_studios_id = []
    screeningCapacities = []
    screeningPrices = []
    screeningDate = []
    screeningTime = []

    for i in range(numRows):
        screeningCapacities.append(request.form.get("screening_capacity_" + str(i)))
        screeningDate.append(request.form.get("screening_date_" + str(i)))
        screeningTime.append(request.form.get("screening_time_" + str(i)))
        screeningPrices.append(request.form.get("screening_price_" + str(i)))

    for i in range(numRows):
        screening_studios_name.append(request.form.get("screening_studio_" + str(i)))

    try:
        for i in range(numRows):
            cursor.execute(
                "SELECT studioId FROM Studio WHERE studioName = ?",
                (screening_studios_name[i],),
            )
            result = cursor.fetchone()
            screening_studios_id.append(result[0])

        # Check for duplicate screenings
        unique_screenings = []
        for i in range(numRows):
            if (
                screening_studios_id[i],
                screeningDate[i],
                screeningTime[i],
            ) in unique_screenings:
                raise DuplicateScreeningError("Duplicate screenings found")
            else:
                # Add the combination to the dictionary
                unique_screenings.append(
                    (screening_studios_id[i], screeningDate[i], screeningTime[i])
                )

        # check for duplicates on db
        for i in range(numRows):
            cursor.execute(
                "SELECT * FROM Screening WHERE studioId = ? and screeningDate = ? and screeningTime = ?",
                (screening_studios_id[i], screeningDate[i], screeningTime[i]),
            )
            result = cursor.fetchone()
            if result:
                raise DuplicateScreeningError("Duplicate screenings found")

        for i in range(numRows):
            cursor.execute(
                "INSERT INTO Screening (filmId, screeningCapacity, screeningOriginalCapacity,studioId, screeningDate, screeningTime, screeningPrice, screeningStatus)"
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    filmId,
                    screeningCapacities[i],
                    screeningCapacities[i],
                    screening_studios_id[i],
                    screeningDate[i],
                    screeningTime[i],
                    screeningPrices[i],
                    "Waiting",
                ),
            )
        db.commit()
        flash("Screenings Added!", "success")
        print("Screenings Added")

    except DuplicateScreeningError as e:
        # Handle the custom exception
        db.rollback()
        flash("Error: Duplicate screenings found. Please try again.", "error")
        print("Error:", e)


def updateFilmScreeningStatus(filmId, db, cursor):
    cursor.execute("SELECT STRFTIME('%Y-%m-%d %H:%M:%S', DATETIME('now', 'localtime'))")
    date = cursor.fetchone()[0]
    date = str(date)

    cursor.execute(
        "SELECT screeningId, screeningDate, screeningTime FROM Screening " "WHERE filmId = ? and screeningStatus = ?",
        (filmId, "Waiting"),
    )

    screenings = cursor.fetchall()

    for screening_data in screenings:
        (
            screening_id,
            screening_date,
            screening_time,
        ) = screening_data
        screening_date_time = screening_date + " " + screening_time
        if date > screening_date_time:
            cursor.execute(
                "UPDATE Screening SET screeningStatus = ? WHERE filmId = ? and screeningId = ?",
                ("Finished", filmId, screening_id),
            )

    db.commit()


# Studio CRUD
def createStudio(db, cursor):
    studio_name = request.form.get("sname")
    studio_address = request.form.get("saddress")

    try:
        cursor.execute(
            "INSERT INTO Studio (studioName, studioAddress)" "VALUES (?, ?)",
            (studio_name, studio_address),
        )
        db.commit()
        flash("Studio added!", "success")
        print("Studio added")

    except Exception as e:
        db.rollback()
        print("Error:", e)


def updateStudio(studioId, db, cursor):
    updated_studio_name = request.form.get("sname")
    updated_studio_address = request.form.get("saddress")

    try:
        cursor.execute(
            "UPDATE Studio SET studioName = ?, studioAddress = ? WHERE studioId = ?",
            (updated_studio_name, updated_studio_address, studioId),
        )

        flash("Studio updated!", "success")
        print("Studio updated")
        db.commit()

    except Exception as e:
        db.rollback()
        # Handle the custom exception
        print("Error:", e)


def getStudioById(studioId, cursor):
    try:
        # Retrieve the studioName and studioAddress based on the studioId
        cursor.execute(
            "SELECT studioName, studioAddress FROM Studio WHERE studioId = ?",
            (studioId,),
        )

        studio_data = cursor.fetchone()
        studio_name = studio_data[0]
        studio_address = studio_data[1]

    except Exception as e:
        print("Error:", e)

    return studio_name, studio_address


def getAllStudios(cursor):
    try:
        cursor.execute("SELECT * FROM Studio")
        studios = cursor.fetchall()

    except Exception as e:
        # Handle the custom exception
        print("Error:", e)

    return studios


# MongoDB Functions
def getChartData(mongodb):
    movieCollection = mongodb["movies"]
    genresList = list(
        movieCollection.aggregate(
            [
                {
                    "$unwind": "$genres"
                },  # Deconstruct the genres array in the collection
                {
                    "$group": {
                        "_id": "$genres",
                        "count": {"$sum": 1},
                    }
                },  # Group the occurrences of each genre in the collection
                {"$sort": {"count": -1}},  # Sort by count in descending order
                {"$limit": 10},  # Get only the top ten genres
                {"$project": {"_id": 1, "genre": "$_id", "count": 1}},
            ]
        )
    )

    countriesList = list(
        movieCollection.aggregate(
            [
                {
                    "$unwind": "$production_countries"
                },  # Deconstruct the production countries array in the collection
                {
                    "$group": {
                        "_id": "$production_countries",
                        "count": {"$sum": 1},
                    }
                },  # Group the occurrences of each production country films had been produced at in the collection
                {"$sort": {"count": -1}},  # Sort by count in descending order
                {
                    "$limit": 10
                },  # Get only the top ten production country films have been made in
                {
                    "$project": {"_id": 1, "production_country": "$_id", "count": 1}
                },  # Project the number of films each top ten production_country has ever produced
            ]
        )
    )

    topPerformingCompanies = list(
        movieCollection.aggregate(
            [
                {
                    "$unwind": "$production_companies"
                },  # Deconstruct the production companies array in the collection
                {
                    "$group": {
                        "_id": "$production_companies",
                        "vote_average": {"$avg": "$vote_average"},
                        "title_count": {"$sum": 1},
                    }
                },  # Find the average of the overall film voting that is produced by each company.
                {
                    "$match": {"title_count": {"$gt": 1, "$exists": True}}
                },  # Exclude those production_companies with only 1 title
                {
                    "$sort": {"vote_average": -1}
                },  # Sort by average overall film voting in descending order
                {
                    "$limit": 10
                },  # Get only the top ten production companies which has the highest average overall film voting
                {
                    "$project": {
                        "_id": 1,
                        "production_companies": "$_id",
                        "vote_average": 1,
                    }
                },  # Project the average of the overall film voting of each top ten production companies
            ]
        )
    )

    topBoxOfficeHits = list(
        movieCollection.aggregate(
            [
                {
                    "$unwind": "$production_companies"
                },  # Deconstruct the production companies array in the collection
                {
                    "$group": {
                        "_id": "$production_companies",
                        "titles": {"$addToSet": "$title"},
                        "total_budget": {"$sum": "$budget"},
                        "total_revenue": {"$sum": "$revenue"},
                        "title_count": {"$sum": 1},
                        "profit": {"$sum": {"$subtract": ["$revenue", "$budget"]}},
                    }
                },  # Find the total budget and revenue that is produced by each company.
                {
                    "$sort": {"title_count": -1}
                },  # Sort by number of film produced by the company in descending order
                {
                    "$limit": 10
                },  # Get only the top ten production companies which has the highest number of films produced
                {
                    "$project": {
                        "_id": 1,
                        "profit": 1,
                    }
                },  # Project the total expected profit the top ten production companies has made so far
            ]
        )
    )

    runTimeBasedOnGenre = list(
        movieCollection.aggregate(
            [
                {
                    "$unwind": "$genres"
                },  # Deconstruct the genres array in the collection
                {
                    "$match": {"runtime": {"$gt": 0}}
                },  # Exclude those films who has a runtime that is 0 mins (false data)
                {
                    "$group": {
                        "_id": "$genres",
                        "max_runtime": {"$max": "$runtime"},
                        "min_runtime": {"$min": "$runtime"},
                        "average_runtime": {"$avg": "$runtime"},
                    }
                },  # Find the min, max and average runtime of each genre
                {
                    "$addFields": {
                        "rounded_runtime": {"$ceil": "$average_runtime"},
                    }
                },  # Round up the average runtime
                {
                    "$project": {
                        "_id": 1,
                        "max_runtime": 1,
                        "min_runtime": 1,
                        "rounded_runtime": 1,
                    }
                },  # Project the min, max and average runtime of each genre
            ]
        )
    )

    averageBudgetOfGenre = list(
        movieCollection.aggregate(
            [
                {
                    "$unwind": "$genres"
                },  # Deconstruct the genres array in the collection
                {
                    "$group": {
                        "_id": "$genres",
                        "average_budget": {"$avg": "$budget"},
                    }
                },  # Find the average budget required for each genre
                {
                    "$addFields": {
                        "rounded_budget": {"$ceil": "$average_budget"},
                    }
                },  # Round up the average budget
                {
                    "$sort": {"average_budget": -1}
                },  # Get only the top ten genres with the highest average budget
                {
                    "$project": {
                        "_id": 1,
                        "rounded_budget": 1,
                    }
                },  # Project the average budget required of each genre
            ]
        )
    )

    return (
        genresList,
        countriesList,
        topPerformingCompanies,
        topBoxOfficeHits,
        runTimeBasedOnGenre,
        averageBudgetOfGenre,
    )


def getAllCasts(mongodb):
    castnames = []
    castcollection = mongodb["cast"]

    # Define the aggregation pipeline
    pipeline = [
        {"$group": {"_id": "$name"}},
        {"$project": {"_id": 0, "unique_name": "$_id"}},
        {"$limit": 10},  # Set the limit here
    ]

    # Execute the aggregation query
    cursor = castcollection.aggregate(pipeline)

    for doc in cursor:
        castnames.append(doc["unique_name"])

    return castnames


def getAllDepartments(mongodb):
    department = []
    departmentcollection = mongodb["crew"]

    # Define the aggregation pipeline
    departmentline = [
        {"$group": {"_id": "$department"}},
        {"$project": {"_id": 0, "unique_name": "$_id"}},
    ]

    # Execute the aggregation query
    departmentcursor = departmentcollection.aggregate(departmentline)

    for doc in departmentcursor:
        department.append(doc["unique_name"])

    return department
