import mysql.connector
try:
    conn = mysql.connector.connect(host='localhost', port=3306, user='root', password='root', database='genealogy_db')
    print("MySQL connected successfully")
    conn.close()
except Exception as e:
    print(f"Error: {e}")