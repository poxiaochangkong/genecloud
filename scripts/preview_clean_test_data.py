"""
Preview what test data will be deleted.
Only SELECT, no DELETE. Shows counts and sample rows.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import mysql.connector
from config import DATABASE_CONFIG

KEEP_USERS = ('admin', 'testuser', 'testuser2')

def preview(conn):
    cursor = conn.cursor(dictionary=True)

    print("=" * 60)
    print("PREVIEW: Test data to be cleaned up")
    print("=" * 60)

    # 1. Users to delete (except keep_users)
    cursor.execute("""
        SELECT user_id, username, created_at FROM users
        WHERE username NOT IN (%s, %s, %s)
        ORDER BY username
    """, KEEP_USERS)
    users = cursor.fetchall()
    print(f"\n[Users to delete] Count: {len(users)}")
    for u in users:
        print(f"  - ID={u['user_id']}, username='{u['username']}', created_at={u['created_at']}")

    # 2. Genealogies created by those users
    if users:
        user_ids = [u['user_id'] for u in users]
        placeholders = ','.join(['%s'] * len(user_ids))
        cursor.execute(f"""
            SELECT g.genealogy_id, g.name, g.surname, g.created_by, u.username, g.created_at
            FROM genealogies g
            JOIN users u ON g.created_by = u.user_id
            WHERE g.created_by IN ({placeholders})
            ORDER BY g.genealogy_id
        """, user_ids)
        genealogies = cursor.fetchall()
        print(f"\n[Genealogies to delete] Count: {len(genealogies)}")
        for g in genealogies:
            print(f"  - ID={g['genealogy_id']}, name='{g['name']}', created_by='{g['username']}'")

        # 3. Members in those genealogies
        if genealogies:
            g_ids = [g['genealogy_id'] for g in genealogies]
            g_placeholders = ','.join(['%s'] * len(g_ids))
            cursor.execute(f"""
                SELECT m.member_id, m.name, m.genealogy_id, g.name as genealogy_name
                FROM members m
                JOIN genealogies g ON m.genealogy_id = g.genealogy_id
                WHERE m.genealogy_id IN ({g_placeholders})
                ORDER BY m.member_id
            """, g_ids)
            members = cursor.fetchall()
            print(f"\n[Members to delete] Count: {len(members)}")
            for m in members[:20]:  # show first 20
                print(f"  - ID={m['member_id']}, name='{m['name']}', genealogy='{m['genealogy_name']}'")
            if len(members) > 20:
                print(f"  ... and {len(members) - 20} more")

            # 4. Marriages for those members
            cursor.execute(f"""
                SELECT mar.marriage_id, mar.member_id1, mar.member_id2,
                       m1.name AS member1_name, m2.name AS member2_name,
                       mar.marriage_year
                FROM marriages mar
                JOIN members m1 ON mar.member_id1 = m1.member_id
                JOIN members m2 ON mar.member_id2 = m2.member_id
                WHERE m1.genealogy_id IN ({g_placeholders})
                LIMIT 50
            """, g_ids)
            marriages_data = cursor.fetchall()
            print(f"\n[Marriages to delete] Count: {len(marriages_data)}")
            for m in marriages_data:
                print(f"  - marriage_id={m['marriage_id']}, {m['member1_name']}({m['member_id1']}) & {m['member2_name']}({m['member_id2']}), year={m['marriage_year']}")

            # 5. Family links for those members
            cursor.execute(f"""
                SELECT fl.link_id, fl.child_id, fl.parent_id, fl.relation_type
                FROM family_links fl
                JOIN members m ON fl.child_id = m.member_id
                WHERE m.genealogy_id IN ({g_placeholders})
                LIMIT 50
            """, g_ids)
            links = cursor.fetchall()
            print(f"\n[Family links to delete] Count: {len(links)}")
            for l in links:
                print(f"  - link_id={l['link_id']}, child={l['child_id']}, parent={l['parent_id']}, type={l['relation_type']}")

            # 6. Collaborations for those genealogies
            cursor.execute(f"""
                SELECT c.collaboration_id, c.user_id, c.genealogy_id, c.role, u.username
                FROM collaborations c
                JOIN users u ON c.user_id = u.user_id
                WHERE c.genealogy_id IN ({g_placeholders})
                LIMIT 50
            """, g_ids)
            collabs = cursor.fetchall()
            print(f"\n[Collaborations to delete] Count: {len(collabs)}")
            for c in collabs:
                print(f"  - collab_id={c['collaboration_id']}, user='{c['username']}', genealogy_id={c['genealogy_id']}, role={c['role']}")

    print("\n" + "=" * 60)
    print("This is a PREVIEW only. No data was deleted.")
    print("=" * 60)
    cursor.close()

if __name__ == '__main__':
    conn = mysql.connector.connect(**DATABASE_CONFIG)
    try:
        preview(conn)
    finally:
        conn.close()