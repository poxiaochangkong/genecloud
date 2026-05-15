# dao/genealogy_dao.py
"""
族谱表的数据访问层
"""


def find_genealogies_by_user(conn, user_id):
    """查找用户可见的族谱：管理员看所有，普通用户看创建的或参与协作的"""
    cursor = conn.cursor(dictionary=True)
    # 检查是否是管理员
    cursor.execute("SELECT is_admin FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    if user and user['is_admin']:
        # 管理员可以看到所有族谱
        cursor.execute("SELECT g.* FROM genealogies g")
        return cursor.fetchall()

    cursor.execute("""
        SELECT g.* FROM genealogies g
        WHERE g.created_by = %s
        UNION
        SELECT g.* FROM genealogies g
        JOIN collaborations c ON g.genealogy_id = c.genealogy_id
        WHERE c.user_id = %s
    """, (user_id, user_id))
    return cursor.fetchall()


def find_genealogy_by_id(conn, genealogy_id):
    """根据ID查询族谱"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM genealogies WHERE genealogy_id = %s",
        (genealogy_id,)
    )
    return cursor.fetchone()


def insert_genealogy(conn, name, surname, created_by):
    """创建新族谱"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO genealogies (name, surname, created_by) VALUES (%s, %s, %s)",
        (name, surname, created_by)
    )
    conn.commit()
    return cursor.lastrowid


def delete_genealogy(conn, genealogy_id):
    """删除族谱（级联删除成员和关系）
    优化：先查一次 member_id 列表，避免重复子查询扫描
    """
    cursor = conn.cursor(dictionary=True)

    # Step 1: 一次性获取该族谱下所有 member_id
    cursor.execute(
        "SELECT member_id FROM members WHERE genealogy_id = %s",
        (genealogy_id,)
    )
    member_ids = [row['member_id'] for row in cursor.fetchall()]

    cursor = conn.cursor()

    if member_ids:
        # Step 2: 用 IN (...) 直接删除关系，避免 4 次子查询
        placeholders = ','.join(['%s'] * len(member_ids))
        cursor.execute(
            f"DELETE FROM family_links WHERE child_id IN ({placeholders}) "
            f"OR parent_id IN ({placeholders})",
            member_ids + member_ids
        )
        cursor.execute(
            f"DELETE FROM marriages WHERE member_id1 IN ({placeholders}) "
            f"OR member_id2 IN ({placeholders})",
            member_ids + member_ids
        )
        cursor.execute(
            "DELETE FROM members WHERE genealogy_id = %s",
            (genealogy_id,)
        )

    # Step 3: 删除协作记录和族谱本身
    cursor.execute(
        "DELETE FROM collaborations WHERE genealogy_id = %s",
        (genealogy_id,)
    )
    cursor.execute(
        "DELETE FROM genealogies WHERE genealogy_id = %s",
        (genealogy_id,)
    )
    conn.commit()
