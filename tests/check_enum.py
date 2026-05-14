"""Check current ENUM state of collaborations.role"""
from config import DATABASE_CONFIG
import mysql.connector

conn = mysql.connector.connect(**DATABASE_CONFIG)
cursor = conn.cursor()
cursor.execute("SHOW COLUMNS FROM collaborations LIKE 'role'")
row = cursor.fetchone()
print('Type:', row[1])
conn.close()