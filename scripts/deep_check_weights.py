import sqlite3
import os

db_path = 'db.sqlite3'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, gross_weight, length, width, height FROM store_product;")
    rows = cursor.fetchall()
    found_any = False
    for row in rows:
        if row[1] > 0 or row[2] > 0 or row[3] > 0 or row[4] > 0:
            print(f"Product: {row[0]} | Weight: {row[1]} | Dims: {row[2]}x{row[3]}x{row[4]}")
            found_any = True
    if not found_any:
        print("No products with non-zero weight or dimensions found.")
    conn.close()
else:
    print("Database not found")
