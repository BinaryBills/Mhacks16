import sqlite3

# Establish a connection to the database.
# This will create the file 'restaurants.db' where your database will be stored.
conn = sqlite3.connect('restaurants.db')
cursor = conn.cursor()

# Execute the CREATE TABLE statement
cursor.execute("""
CREATE TABLE IF NOT EXISTS Restaurants (
    restaurant_id INTEGER PRIMARY KEY,
    place_name TEXT NOT NULL,
    tags TEXT
)
""")

# Commit the changes
conn.commit()

# Insert an example restaurant
cursor.execute("INSERT INTO Restaurants (place_name, tags) VALUES (?, ?)", ('Example Restaurant', 'cool,warm,fuzzy'))

# Commit the insert
conn.commit()

# Query for restaurants with the tag 'warm'
cursor.execute("SELECT * FROM Restaurants WHERE tags LIKE ?", ('%warm%',))

# Fetch all results
results = cursor.fetchall()

# Close the connection
conn.close()

# Print results
for row in results:
    print(row)
