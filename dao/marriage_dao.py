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