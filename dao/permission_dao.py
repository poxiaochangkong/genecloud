# dao/permission_dao.py
"""
权限数据访问层：维护 用户-族谱-权限 三元组
权限级别：1=admin, 2=owner, 3=editor
"""


def get_user_role(conn, user_id, genealogy_id):
    """查询用户对某族谱的权限级别，返回 ('admin','owner','editor') 或 None"""
    cursor = conn.cursor(dictionary=True)
    # 管理员自动拥有所有族谱的1级权限
    cursor.execute("SELECT is_admin FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    if user and user['is_admin']:
        return 'admin'

    cursor.execute(
        "SELECT role FROM collaborations WHERE user_id = %s AND genealogy_id = %s",
        (user_id, genealogy_id)
    )
    row = cursor.fetchone()
    return row['role'] if row else None


def get_genealogy_permissions(conn, genealogy_id):
    """获取某族谱的所有权限记录"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.user_id, c.role, u.username
        FROM collaborations c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.genealogy_id = %s
    """, (genealogy_id,))
    return cursor.fetchall()


def grant_permission(conn, user_id, genealogy_id, role):
    """赋予或更新权限（已存在则更新）"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO collaborations (user_id, genealogy_id, role)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE role = VALUES(role)
    """, (user_id, genealogy_id, role))
    conn.commit()


def revoke_permission(conn, user_id, genealogy_id):
    """撤销权限"""
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM collaborations WHERE user_id = %s AND genealogy_id = %s",
        (user_id, genealogy_id)
    )
    conn.commit()


def find_user_by_username(conn, username):
    """根据用户名查询用户（用于权限赋予时查找用户）"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id, username FROM users WHERE username = %s", (username,))
    return cursor.fetchone()