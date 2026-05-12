import mysql.connector
from config import DATABASE_CONFIG

conn = mysql.connector.connect(**DATABASE_CONFIG)
cursor = conn.cursor()

# 1. 给 users 表加 is_admin 字段
try:
    cursor.execute("ALTER TABLE users ADD COLUMN is_admin TINYINT DEFAULT 0")
    print("OK: users.is_admin added")
except mysql.connector.errors.ProgrammingError as e:
    if "Duplicate column" in str(e):
        print("SKIP: users.is_admin already exists")
    else:
        raise

# 2. 修改 collaborations 表的 role ENUM
try:
    cursor.execute("ALTER TABLE collaborations MODIFY COLUMN role ENUM('admin','owner','editor') DEFAULT 'editor'")
    print("OK: collaborations.role enum updated")
except Exception as e:
    print(f"SKIP: {e}")

# 3. 给已有的族谱创建者插入 owner 权限记录
cursor.execute("""
    INSERT IGNORE INTO collaborations (user_id, genealogy_id, role)
    SELECT created_by, genealogy_id, 'owner' FROM genealogies
""")
conn.commit()
print(f"OK: inserted {cursor.rowcount} owner records")

cursor.close()
conn.close()
print("Migration done.")