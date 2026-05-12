# init_admin.py
"""
初始化管理员账户，确保系统有且仅有1个管理员
"""
import hashlib
from dao.db import get_connection
from dao.user_dao import find_user_by_username, insert_user


def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_admin():
    """创建初始管理员账户"""
    conn = get_connection()
    try:
        # 检查是否已有管理员
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id, username FROM users WHERE is_admin = 1")
        admins = cursor.fetchall()

        if len(admins) > 0:
            print(f"WARNING: Already {len(admins)} admin(s):")
            for a in admins:
                print(f"  user_id={a['user_id']}, username={a['username']}")
            print("Skip creating admin.")
            return

        # 创建管理员
        admin_username = "admin"
        admin_password = "admin123"
        password_hash = _hash_password(admin_password)

        # 先检查用户是否已存在
        existing = find_user_by_username(conn, admin_username)
        if existing:
            # 已存在，设为admin
            cursor.execute("UPDATE users SET is_admin = 1 WHERE user_id = %s", (existing['user_id'],))
            conn.commit()
            print(f"User '{admin_username}' already exists, set is_admin=1. user_id={existing['user_id']}")
        else:
            user_id = insert_user(conn, admin_username, password_hash)
            cursor.execute("UPDATE users SET is_admin = 1 WHERE user_id = %s", (user_id,))
            conn.commit()
            print(f"Admin created: username='{admin_username}', password='{admin_password}', user_id={user_id}")

    finally:
        conn.close()


if __name__ == '__main__':
    init_admin()