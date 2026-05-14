"""
Seed demo data: create a genealogy with ~35 members, parent-child relations and marriages.
Uses testuser (password: test123456) as the creator.
"""
import sys
import os
import hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import mysql.connector
from config import DATABASE_CONFIG
from dao.marriage_dao import insert_marriage as _insert_marriage_dao


# ---------- helpers ----------
def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def _find_or_create_testuser(conn):
    """Return user_id of testuser; create if not exists."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id FROM users WHERE username = 'testuser'")
    row = cursor.fetchone()
    if row:
        return row['user_id']
    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
        ('testuser', _hash_password('test123456'))
    )
    conn.commit()
    return cursor.lastrowid


def _create_genealogy(conn, name, surname, created_by):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO genealogies (name, surname, created_by) VALUES (%s, %s, %s)",
        (name, surname, created_by)
    )
    conn.commit()
    return cursor.lastrowid


def _insert_member(conn, genealogy_id, name, gender, birth_year, death_year=None, bio=None):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO members (genealogy_id, name, gender, birth_year, death_year, bio) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (genealogy_id, name, gender, birth_year, death_year, bio)
    )
    return cursor.lastrowid


def _insert_link(conn, child_id, parent_id, relation_type):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO family_links (child_id, parent_id, relation_type) VALUES (%s, %s, %s)",
        (child_id, parent_id, relation_type)
    )


def _insert_marriage(conn, id1, id2, year):
    _insert_marriage_dao(conn, id1, id2, year)


# ---------- main ----------
def seed():
    conn = mysql.connector.connect(**DATABASE_CONFIG)
    try:
        user_id = _find_or_create_testuser(conn)
        print(f"[1] testuser user_id = {user_id}")

        gid = _create_genealogy(conn, "张氏族谱", "张", user_id)
        print(f"[2] Created genealogy id = {gid}")

        # ---- Members ----
        # G1
        g1_1 = _insert_member(conn, gid, "张太公",   'M', 1880, 1950, "张家始祖")
        g1_2 = _insert_member(conn, gid, "张太奶奶", 'F', 1885, 1955, "始祖之妻")
        print(f"[3] G1: {g1_1}, {g1_2}")

        # G2
        g2_1 = _insert_member(conn, gid, "张德福", 'M', 1910, 1985, "长子")
        g2_2 = _insert_member(conn, gid, "张德禄", 'M', 1915, 1990, "次子")
        g2_3 = _insert_member(conn, gid, "周秀英",  'F', 1912, 1988, "张德福之妻")
        g2_4 = _insert_member(conn, gid, "李翠花",  'F', 1918, 1992, "张德禄之妻")
        print(f"[4] G2: {g2_1}, {g2_2}, {g2_3}, {g2_4}")

        # G3
        g3_1 = _insert_member(conn, gid, "张国强", 'M', 1938, 2010, "张德福长子")
        g3_2 = _insert_member(conn, gid, "张国栋", 'M', 1942, 2015, "张德福次子")
        g3_3 = _insert_member(conn, gid, "张秀兰", 'F', 1945, None,  "张德福之女")
        g3_4 = _insert_member(conn, gid, "张国民", 'M', 1940, 2012, "张德禄长子")
        g3_5 = _insert_member(conn, gid, "张秀英", 'F', 1948, None,  "张德禄之女")
        g3_6 = _insert_member(conn, gid, "王淑珍",  'F', 1940, 2018, "张国强之妻")
        g3_7 = _insert_member(conn, gid, "赵秀芳",  'F', 1945, 2020, "张国栋之妻")
        g3_8 = _insert_member(conn, gid, "刘秀华",  'F', 1943, None,  "张国民之妻")
        print(f"[5] G3: {g3_1}..{g3_8}")

        # G4
        g4_1  = _insert_member(conn, gid, "张伟",   'M', 1965, None, "张国强长子")
        g4_2  = _insert_member(conn, gid, "张强",   'M', 1968, None, "张国强次子")
        g4_3  = _insert_member(conn, gid, "张丽",   'F', 1970, None, "张国强之女")
        g4_4  = _insert_member(conn, gid, "张勇",   'M', 1966, None, "张国栋之子")
        g4_5  = _insert_member(conn, gid, "张敏",   'F', 1972, None, "张国栋之女")
        g4_6  = _insert_member(conn, gid, "张军",   'M', 1963, None, "张国民长子")
        g4_7  = _insert_member(conn, gid, "张涛",   'M', 1967, None, "张国民次子")
        g4_8  = _insert_member(conn, gid, "陈晓梅", 'F', 1967, None, "张伟之妻")
        g4_9  = _insert_member(conn, gid, "杨雪",   'F', 1970, None, "张强之妻")
        g4_10 = _insert_member(conn, gid, "马丽",   'F', 1968, None, "张勇之妻")
        g4_11 = _insert_member(conn, gid, "孙静",   'F', 1965, None, "张军之妻")
        print(f"[6] G4: {g4_1}..{g4_11}")

        # G5
        g5_1  = _insert_member(conn, gid, "张浩然", 'M', 1990, None, "张伟长子")
        g5_2  = _insert_member(conn, gid, "张浩然2",'M', 1993, None, "张伟次子（同名区别）")
        g5_3  = _insert_member(conn, gid, "张子轩", 'M', 1992, None, "张强之子")
        g5_4  = _insert_member(conn, gid, "张子涵", 'F', 1995, None, "张强之女")
        g5_5  = _insert_member(conn, gid, "张宇",   'M', 1991, None, "张勇之子")
        g5_6  = _insert_member(conn, gid, "张瑶",   'F', 1994, None, "张勇长女")
        g5_7  = _insert_member(conn, gid, "张婷",   'F', 1997, None, "张勇次女")
        g5_8  = _insert_member(conn, gid, "张浩",   'M', 1988, None, "张军长子")
        g5_9  = _insert_member(conn, gid, "张杰",   'M', 1990, None, "张军次子")
        g5_10 = _insert_member(conn, gid, "张芳",   'F', 1993, None, "张军之女")
        print(f"[7] G5: {g5_1}..{g5_10}")

        # ---- Parent-child relationships ----
        links = [
            (g2_1, g1_1, 'father'), (g2_1, g1_2, 'mother'),
            (g2_2, g1_1, 'father'), (g2_2, g1_2, 'mother'),
            (g3_1, g2_1, 'father'), (g3_1, g2_3, 'mother'),
            (g3_2, g2_1, 'father'), (g3_2, g2_3, 'mother'),
            (g3_3, g2_1, 'father'), (g3_3, g2_3, 'mother'),
            (g3_4, g2_2, 'father'), (g3_4, g2_4, 'mother'),
            (g3_5, g2_2, 'father'), (g3_5, g2_4, 'mother'),
            (g4_1, g3_1, 'father'), (g4_1, g3_6, 'mother'),
            (g4_2, g3_1, 'father'), (g4_2, g3_6, 'mother'),
            (g4_3, g3_1, 'father'), (g4_3, g3_6, 'mother'),
            (g4_4, g3_2, 'father'), (g4_4, g3_7, 'mother'),
            (g4_5, g3_2, 'father'), (g4_5, g3_7, 'mother'),
            (g4_6, g3_4, 'father'), (g4_6, g3_8, 'mother'),
            (g4_7, g3_4, 'father'), (g4_7, g3_8, 'mother'),
            (g5_1, g4_1, 'father'), (g5_1, g4_8, 'mother'),
            (g5_2, g4_1, 'father'), (g5_2, g4_8, 'mother'),
            (g5_3, g4_2, 'father'), (g5_3, g4_9, 'mother'),
            (g5_4, g4_2, 'father'), (g5_4, g4_9, 'mother'),
            (g5_5, g4_4, 'father'), (g5_5, g4_10, 'mother'),
            (g5_6, g4_4, 'father'), (g5_6, g4_10, 'mother'),
            (g5_7, g4_4, 'father'), (g5_7, g4_10, 'mother'),
            (g5_8, g4_6, 'father'), (g5_8, g4_11, 'mother'),
            (g5_9, g4_6, 'father'), (g5_9, g4_11, 'mother'),
            (g5_10, g4_6, 'father'), (g5_10, g4_11, 'mother'),
        ]
        for child_id, parent_id, rel in links:
            _insert_link(conn, child_id, parent_id, rel)
        print(f"[8] Inserted {len(links)} family_links")

        # ---- Marriages ----
        marriages = [
            (g1_1, g1_2, 1905),
            (g2_1, g2_3, 1935),
            (g2_2, g2_4, 1938),
            (g3_1, g3_6, 1962),
            (g3_2, g3_7, 1964),
            (g3_4, g3_8, 1962),
            (g4_1, g4_8, 1988),
            (g4_2, g4_9, 1990),
            (g4_4, g4_10, 1989),
            (g4_6, g4_11, 1986),
        ]
        for id1, id2, year in marriages:
            _insert_marriage(conn, id1, id2, year)
        print(f"[9] Inserted {len(marriages)} marriages")

        # ---- Summary ----
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS cnt FROM members WHERE genealogy_id = %s", (gid,))
        member_count = cursor.fetchone()['cnt']
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM family_links fl "
            "JOIN members m ON fl.child_id = m.member_id WHERE m.genealogy_id = %s",
            (gid,)
        )
        link_count = cursor.fetchone()['cnt']
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM marriages mar "
            "JOIN members m ON mar.member_id1 = m.member_id WHERE m.genealogy_id = %s",
            (gid,)
        )
        marriage_count = cursor.fetchone()['cnt']

        print(f"\n{'='*50}")
        print(f"Done! Genealogy '张氏族谱' (id={gid})")
        print(f"  Members  : {member_count}")
        print(f"  Links    : {link_count}")
        print(f"  Marriages: {marriage_count}")
        print(f"  Creator  : testuser (user_id={user_id})")
        print(f"{'='*50}")

    finally:
        conn.close()


if __name__ == '__main__':
    seed()