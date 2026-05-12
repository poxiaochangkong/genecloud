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