# dao/member_dao.py
"""
成员表的数据访问层
"""


def find_member_by_id(conn, member_id):
    """根据ID查询成员"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM members WHERE member_id = %s",
        (member_id,)
    )
    return cursor.fetchone()


def search_by_name(conn, genealogy_id, keyword, limit=100):
    """根据姓名模糊搜索（限制返回数量防止前端卡死）"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM members WHERE genealogy_id = %s AND name LIKE %s "
        "ORDER BY name LIMIT %s",
        (genealogy_id, f"%{keyword}%", limit)
    )
    return cursor.fetchall()


def find_members_by_genealogy(conn, genealogy_id, page=None, page_size=None):
    """获取某族谱的成员（支持分页，page从1开始）"""
    cursor = conn.cursor(dictionary=True)
    if page is not None and page_size is not None:
        offset = (page - 1) * page_size
        cursor.execute(
            "SELECT * FROM members WHERE genealogy_id = %s "
            "ORDER BY birth_year LIMIT %s OFFSET %s",
            (genealogy_id, page_size, offset)
        )
        rows = cursor.fetchall()
        # Get total count
        cursor.execute(
            "SELECT COUNT(*) AS total FROM members WHERE genealogy_id = %s",
            (genealogy_id,)
        )
        total = cursor.fetchone()['total']
        return rows, total
    else:
        cursor.execute(
            "SELECT * FROM members WHERE genealogy_id = %s ORDER BY birth_year",
            (genealogy_id,)
        )
        return cursor.fetchall(), None


def insert_member(conn, genealogy_id, name, gender, birth_year, death_year, bio):
    """插入新成员"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO members (genealogy_id, name, gender, birth_year, death_year, bio) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (genealogy_id, name, gender, birth_year, death_year, bio)
    )
    conn.commit()
    return cursor.lastrowid


def update_member(conn, member_id, name, gender, birth_year, death_year, bio):
    """更新成员信息"""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE members SET name=%s, gender=%s, birth_year=%s, death_year=%s, bio=%s "
        "WHERE member_id=%s",
        (name, gender, birth_year, death_year, bio, member_id)
    )
    conn.commit()


def delete_member(conn, member_id):
    """删除成员及其所有关系"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM family_links WHERE child_id = %s OR parent_id = %s",
                   (member_id, member_id))
    cursor.execute("DELETE FROM marriages WHERE member_id1 = %s OR member_id2 = %s",
                   (member_id, member_id))
    cursor.execute("DELETE FROM members WHERE member_id = %s", (member_id,))
    conn.commit()