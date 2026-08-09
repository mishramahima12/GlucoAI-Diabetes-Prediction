import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="ashu",
    database="diabetes_db"
)

cursor = conn.cursor()

print("Database Connected Successfully!")
