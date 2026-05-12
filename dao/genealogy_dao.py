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
    """删除族谱（级联删除成员和关系）"""
    cursor = conn.cursor()
    # 先删关系，再删成员，最后删族谱
    # 注意：实际项目中应该用事务
    cursor.execute("""
        DELETE fl FROM family_links fl
        JOIN members m ON fl.child_id = m.member_id OR fl.parent_id = m.member_id
        WHERE m.genealogy_id = %s
    """, (genealogy_id,))
    cursor.execute(
        "DELETE FROM marriages WHERE member_id1 IN "
        "(SELECT member_id FROM members WHERE genealogy_id = %s) "
        "OR member_id2 IN "
        "(SELECT member_id FROM members WHERE genealogy_id = %s)",
        (genealogy_id, genealogy_id)
    )
    cursor.execute(
        "DELETE FROM members WHERE genealogy_id = %s",
        (genealogy_id,)
    )
    cursor.execute(
        "DELETE FROM collaborations WHERE genealogy_id = %s",
        (genealogy_id,)
    )
    cursor.execute(
        "DELETE FROM genealogies WHERE genealogy_id = %s",
        (genealogy_id,)
    )
    conn.commit()