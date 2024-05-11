from flask import g
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
import sqlite3

# Define the path to the SQLite database
SQLITE_CONNECTION_STRING = 'filminsight_sql.db'
MONGODB_CONNECTION_STRING = "mongodb+srv://user:P%40ssw0rd@inf2003-project.igufy0o.mongodb.net/"

def get_sqlite_database():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(SQLITE_CONNECTION_STRING)
        print("Connected to the database.")
    return db

def get_mongodb_database():
    try:
        client = MongoClient(MONGODB_CONNECTION_STRING)
        return client['db']
    
    except Exception as e:
        # Handle database errors and display an error message
        print("Error", e)

def create_all_tables(cursor):
    try:
        create_table_user_sql = '''
        CREATE TABLE IF NOT EXISTS User (
            userId INTEGER NOT NULL,
            userName TEXT NOT NULL,
            userEmail TEXT NOT NULL UNIQUE,
            userPassword TEXT NOT NULL,
            userPhoneNumber	INTEGER NOT NULL UNIQUE,
            userDOB	TEXT NOT NULL,
            userGender TEXT NOT NULL CHECK(userGender IN ('Male', 'Female', 'Other')),
            PRIMARY KEY(userId AUTOINCREMENT)
        )
        '''

        create_table_filmmaker_sql = '''
        CREATE TABLE IF NOT EXISTS Filmmaker (
            filmmakerId INTEGER NOT NULL,
            filmmakerName TEXT NOT NULL,
            filmmakerEmail TEXT NOT NULL UNIQUE,
            filmmakerPassword TEXT NOT NULL,
            filmmakerPhoneNumber	TEXT NOT NULL UNIQUE,
            filmmakerDOB	TEXT NOT NULL,
            filmmakerGender TEXT NOT NULL CHECK(filmmakerGender IN ('Male', 'Female', 'Unknown')),
            PRIMARY KEY(filmmakerId AUTOINCREMENT)
        )
        '''

        create_table_film_sql = '''
        CREATE TABLE IF NOT EXISTS "Film" (
            	"filmId"	INTEGER NOT NULL,
                "filmmakerid"	INTEGER NOT NULL,
                "filmName"	TEXT NOT NULL,
                "filmCast"	TEXT NOT NULL,
                "filmPoster"	BLOB NOT NULL,
                "filmSynopsis"	TEXT NOT NULL,
                "filmLanguage"	TEXT NOT NULL,
                "filmGenre"	TEXT NOT NULL,
                "filmRunTime"	INTEGER NOT NULL,
                "filmReleaseDate"	TEXT NOT NULL,
                "filmMaturityRating"	TEXT NOT NULL,
                PRIMARY KEY("filmid"),
                FOREIGN KEY("filmmakerid") REFERENCES "Filmmaker"("filmmakerId")
        )
        '''

        create_table_screening_sql = '''
        CREATE TABLE IF NOT EXISTS "Screening" (
            "screeningId"	INTEGER NOT NULL,
            "filmId"	INTEGER NOT NULL,
            "screeningCapacity"	INTEGER NOT NULL,
            "screeningOriginalCapacity"	INTEGER NOT NULL,
            "studioId"	INTEGER NOT NULL COLLATE BINARY,
            "screeningDate"	TEXT NOT NULL,
            "screeningTime"	TEXT NOT NULL,
            "screeningPrice"	NUMERIC NOT NULL,
            "screeningStatus"	TEXT NOT NULL,
            PRIMARY KEY("screeningId"),
            FOREIGN KEY("studioId") REFERENCES "Studio"("studioId"),
            FOREIGN KEY("filmId") REFERENCES "Film"("filmId") ON DELETE CASCADE
        )
        '''

        create_table_studio_sql = '''
        CREATE TABLE IF NOT EXISTS Studio (
            "studioId"	INTEGER NOT NULL,
            "studioName"	TEXT NOT NULL,
            "studioAddress"	TEXT NOT NULL,
            PRIMARY KEY("studioId" AUTOINCREMENT)
        )
        '''

        create_table_film_review_sql = '''
            CREATE TABLE IF NOT EXISTS "Film_Review" (
                "filmReviewId"	INTEGER NOT NULL,
                "filmReviewTitle"	TEXT NOT NULL,
                "filmReviewRating"	INTEGER NOT NULL,
                "filmReviewDescription"	TEXT NOT NULL,
                "filmReviewDate" TEXT NOT NULL,
                "userId"	INTEGER NOT NULL,
                "filmId"	INTEGER NOT NULL,
                FOREIGN KEY("filmId") REFERENCES "Film"("filmId") ON DELETE CASCADE,
                FOREIGN KEY("userId") REFERENCES "User"("userId") ON DELETE CASCADE,
                PRIMARY KEY("filmReviewId")
            );
        '''



        create_table_booking_sql = '''
        CREATE TABLE IF NOT EXISTS "Booking" (
            "bookingId"	INTEGER NOT NULL,
            "userid"	INTEGER NOT NULL,
            "filmName"	TEXT NOT NULL,
            "bookingDate"	TEXT NOT NULL,
            "bookingTime"	TEXT NOT NULL,
            "transactionsId"	INTEGER NOT NULL,
            "bookingStatus"	TEXT NOT NULL,
            "numberOfTickets"	INTEGER NOT NULL,
            FOREIGN KEY("userid") REFERENCES "User"("userId"),
            FOREIGN KEY("transactionsId") REFERENCES "Transactions"("transactionsId"),
            PRIMARY KEY("bookingId")
        );
        '''

        create_table_transactions_sql = '''
        CREATE TABLE IF NOT EXISTS Transactions (
            "transactionsId"	INTEGER NOT NULL,
            "transactionsAmount"	INTEGER NOT NULL,
            "transactionsTimestamp"	TEXT NOT NULL,
            "transactionsPaymentMethod"	TEXT NOT NULL,
            PRIMARY KEY("transactionsId" AUTOINCREMENT)
        )
        '''

        
        # Execute the SQL statement to create the various tables
        cursor.execute(create_table_filmmaker_sql)
        cursor.execute(create_table_film_sql)
        cursor.execute(create_table_user_sql)
        cursor.execute(create_table_screening_sql)
        cursor.execute(create_table_studio_sql)
        cursor.execute(create_table_film_review_sql)
        cursor.execute(create_table_booking_sql)
        cursor.execute(create_table_transactions_sql)
        
    except Exception as e:
        # Handle database errors and display an error message
        print("Error", e)