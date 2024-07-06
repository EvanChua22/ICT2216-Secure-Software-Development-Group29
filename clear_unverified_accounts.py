import sqlite3
from datetime import datetime, timedelta

# Replace with your actual database file path
db_path = 'database.db'

# Establish a database connection
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Calculate the datetime 48 hours ago
time_threshold = datetime.now() - timedelta(hours=48)
formatted_threshold = time_threshold.strftime('%Y-%m-%d %H:%M:%S')

# Define the DELETE query
delete_query = """
DELETE FROM users
WHERE is_verified = 0
AND created_at < ?;
"""

# Execute the DELETE query
cursor.execute(delete_query, (formatted_threshold,))

# Commit the changes
conn.commit()

# Close the cursor and connection
cursor.close()
conn.close()

print("Unverified users older than 48 hours have been deleted.")
