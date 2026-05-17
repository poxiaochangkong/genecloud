# dao/user_dao.py
"""
用户表的数据访问层：只写 SQL，不做业务判断
"""


def find_user_by_username(conn, username):
    """根据用户名查询用户"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE username = %s",
        (username,)
    )
    return cursor.fetchone()      # 返回 dict 或 None


def find_user_by_id(conn, user_id):
    """根据ID查询用户"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE user_id = %s",
        (user_id,)
    )
    return cursor.fetchone()


def insert_user(conn, username, password_hash, email=None):
    """注册新用户"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",
        (username, password_hash, email)
    )
    conn.commit()
    return cursor.lastrowid        # 返回新用户的 user_id


def delete_user_by_id(conn, user_id):
    """根据ID删除用户"""
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM users WHERE user_id = %s",
        (user_id,)
    )
    conn.commit()
    return cursor.rowcount            # 返回受影响行数


def find_all_users(conn):
    """查询所有用户（不含密码哈希），按创建时间升序"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT user_id, username, email, is_admin, created_at FROM users ORDER BY created_at"
    )
    return cursor.fetchall()


def count_genealogies_by_user(conn, user_id):
    """统计某用户创建的族谱数量"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM genealogies WHERE created_by = %s",
        (user_id,)
    )
    row = cursor.fetchone()
    return row[0]


def find_genealogies_by_creator(conn, user_id):
    """查询某用户创建的所有族谱ID和名称"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT genealogy_id, name FROM genealogies WHERE created_by = %s",
        (user_id,)
    )
    return cursor.fetchall()


def find_all_users_with_genealogy_count(conn):
    """查询所有用户并附带族谱数量（单次 JOIN 查询，避免 N+1）"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.user_id, u.username, u.email, u.is_admin, u.created_at,
               COUNT(g.genealogy_id) AS genealogy_count
        FROM users u LEFT JOIN genealogies g ON u.user_id = g.created_by
        GROUP BY u.user_id
        ORDER BY u.created_at
    """)
    return cursor.fetchall()
