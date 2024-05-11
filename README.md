# INF2003 Database Project Group 4

# User Manual
## Dependencies
1. open command prompt (run as administrator)
2. cd to the project folder ..\..\INF2003-DBS-GRP4
3. enter python -m pip install -r requirements.txt

Ensure filminsight_sql.db is in the root folder (do not delete this file)

## Dummy Accounts
### Filmmaker
Email: filmmaker@gmail.com
Password: 1234567890

### User
Email: user@gmail.com
Password: 1234567890

### How to run
Run the app.py file and open http://127.0.0.1:5000 (local host) on the browser.
If you do not have an IDE:
1. open command prompt (run as administrator)
2. cd to the project folder ..\..\INF2003-DBS-GRP4
3. enter python app.py

### User functionalities
- Booking movie screening
    - Requires user to be logged in
- Add movie reviews
- Delete movie reviews
- Edit profile details
- View current bookings
- View all reviews

### Filmmaker functionalities
- Data analysis
- Add film
    - Film name cannot already exist in the database
- Add screenings
    - Screenings place and time cannot be identical to already existing screening
- Edit film
- Delete film
    - Film must have all screenings finished beforehand
- Add studio
    - Studio cannot already have the same name as existing studio
- Edit studio
- Find crew
- Edit profile details