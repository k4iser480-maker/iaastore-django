import sqlite3
import os

db_path = 'db.sqlite3'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, length, width, height, gross_weight FROM store_product LIMIT 20;")
    rows = cursor.fetchall()
    for row in rows:
        print(f"{row[0]}: {row[1]}x{row[2]}x{row[3]} - {row[4]}kg")
    conn.close()
else:
    print("Database not found")
