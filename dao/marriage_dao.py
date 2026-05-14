# dao/marriage_dao.py
"""
婚姻关系的数据访问层
"""


def find_marriages_by_member(conn, member_id):
    """查找某人的所有婚姻关系"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT mar.*,
               m1.name AS member1_name,
               m2.name AS member2_name
        FROM marriages mar
        JOIN members m1 ON mar.member_id1 = m1.member_id
        JOIN members m2 ON mar.member_id2 = m2.member_id
        WHERE mar.member_id1 = %s OR mar.member_id2 = %s
    """, (member_id, member_id))
    return cursor.fetchall()


def insert_marriage(conn, member_id1, member_id2, marriage_year):
    """记录婚姻关系"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO marriages (member_id1, member_id2, marriage_year) "
        "VALUES (%s, %s, %s)",
        (member_id1, member_id2, marriage_year)
    )
    conn.commit()
    return cursor.lastrowid


def find_marriage_by_id(conn, marriage_id):
    """根据ID查找婚姻关系"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM marriages WHERE marriage_id = %s", (marriage_id,))
    return cursor.fetchone()


def find_spouses(conn, member_id):
    """查找某人的配偶"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.member_id, m.name, m.gender, m.birth_year, m.death_year,
               mar.marriage_id, mar.marriage_year, mar.divorce_year,
               CASE WHEN mar.member_id1 = %s THEN mar.member_id2 ELSE mar.member_id1 END AS spouse_id
        FROM marriages mar
        JOIN members m ON m.member_id = CASE WHEN mar.member_id1 = %s THEN mar.member_id2 ELSE mar.member_id1 END
        WHERE mar.member_id1 = %s OR mar.member_id2 = %s
    """, (member_id, member_id, member_id, member_id))
    return cursor.fetchall()


def delete_marriage(conn, marriage_id):
    """删除婚姻关系"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM marriages WHERE marriage_id = %s", (marriage_id,))
    conn.commit()
    return cursor.rowcount
