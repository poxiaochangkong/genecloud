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

# 4. 添加性能优化索引
INDEXES = [
    ("members", "idx_members_genealogy", "genealogy_id"),
    ("family_links", "idx_family_links_child", "child_id"),
    ("family_links", "idx_family_links_parent", "parent_id"),
    ("marriages", "idx_marriages_member1", "member_id1"),
    ("marriages", "idx_marriages_member2", "member_id2"),
    ("genealogies", "idx_genealogies_creator", "created_by"),
    ("collaborations", "idx_collaborations_genealogy", "genealogy_id"),
]

for table, idx_name, column in INDEXES:
    try:
        cursor.execute(f"CREATE INDEX {idx_name} ON {table} ({column})")
        print(f"OK: {idx_name} created on {table}({column})")
    except mysql.connector.errors.ProgrammingError as e:
        if "Duplicate" in str(e):
            print(f"SKIP: {idx_name} already exists")
        else:
            print(f"WARN: {idx_name} - {e}")

cursor.close()
conn.close()
print("Migration done.")
