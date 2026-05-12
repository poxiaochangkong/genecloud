# dao/family_link_dao.py
"""
血缘关系的数据访问层（包含递归CTE查询）
这是整个项目最核心的 DAO
"""


def find_parents(conn, child_id):
    """查找某人的所有父母"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT fl.*, m.name AS parent_name
        FROM family_links fl
        JOIN members m ON fl.parent_id = m.member_id
        WHERE fl.child_id = %s
    """, (child_id,))
    return cursor.fetchall()


def find_children(conn, parent_id):
    """查找某人的所有子女"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT fl.*, m.name AS child_name
        FROM family_links fl
        JOIN members m ON fl.child_id = m.member_id
        WHERE fl.parent_id = %s
    """, (parent_id,))
    return cursor.fetchall()


def insert_family_link(conn, child_id, parent_id, relation_type):
    """建立血缘关系"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO family_links (child_id, parent_id, relation_type) "
        "VALUES (%s, %s, %s)",
        (child_id, parent_id, relation_type)
    )
    conn.commit()


# ============================================
# 核心：递归CTE查询
# ============================================

def find_all_ancestors(conn, member_id):
    """
    查询某成员的所有祖先（递归向上追溯）
    返回从本人开始，一直到最古老祖先的完整链路
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        WITH RECURSIVE ancestors AS (
            -- 锚点：从给定成员开始
            SELECT m.member_id, m.name, m.gender, m.birth_year,
                   fl.parent_id, fl.relation_type, 1 AS generation
            FROM members m
            LEFT JOIN family_links fl ON m.member_id = fl.child_id
            WHERE m.member_id = %s

            UNION ALL

            -- 递归：向上找父母的父母
            SELECT m.member_id, m.name, m.gender, m.birth_year,
                   fl.parent_id, fl.relation_type, a.generation + 1
            FROM ancestors a
            JOIN members m ON a.parent_id = m.member_id
            LEFT JOIN family_links fl ON m.member_id = fl.child_id
            WHERE a.parent_id IS NOT NULL
        )
        SELECT * FROM ancestors ORDER BY generation
    """, (member_id,))
    return cursor.fetchall()


def find_all_descendants(conn, member_id):
    """
    查询某成员的所有后代（递归向下展开）
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        WITH RECURSIVE descendants AS (
            -- 锚点：从给定成员开始
            SELECT m.member_id, m.name, m.gender, m.birth_year,
                   1 AS generation
            FROM members m
            WHERE m.member_id = %s

            UNION ALL

            -- 递归：向下找子女的子女
            SELECT m.member_id, m.name, m.gender, m.birth_year,
                   d.generation + 1
            FROM descendants d
            JOIN family_links fl ON d.member_id = fl.parent_id
            JOIN members m ON fl.child_id = m.member_id
        )
        SELECT * FROM descendants ORDER BY generation
    """, (member_id,))
    return cursor.fetchall()


def find_kinship_path(conn, member_id_a, member_id_b):
    """
    查询两人之间的亲缘链路
    思路：分别向上追溯祖先，找到最近共同祖先(LCA)，再拼接路径
    """
    cursor = conn.cursor(dictionary=True)

    # 第一步：获取 A 的所有祖先及距离
    cursor.execute("""
        WITH RECURSIVE path_a AS (
            SELECT m.member_id, m.name, 0 AS distance
            FROM members m WHERE m.member_id = %s
            UNION ALL
            SELECT m.member_id, m.name, pa.distance + 1
            FROM path_a pa
            JOIN family_links fl ON pa.member_id = fl.child_id
            JOIN members m ON fl.parent_id = m.member_id
        )
        SELECT * FROM path_a
    """, (member_id_a,))
    path_a = cursor.fetchall()

    # 第二步：获取 B 的所有祖先及距离
    cursor.execute("""
        WITH RECURSIVE path_b AS (
            SELECT m.member_id, m.name, 0 AS distance
            FROM members m WHERE m.member_id = %s
            UNION ALL
            SELECT m.member_id, m.name, pb.distance + 1
            FROM path_b pb
            JOIN family_links fl ON pb.member_id = fl.child_id
            JOIN members m ON fl.parent_id = m.member_id
        )
        SELECT * FROM path_b
    """, (member_id_b,))
    path_b = cursor.fetchall()

    # 第三步：找最近共同祖先
    path_a_dict = {row['member_id']: row for row in path_a}
    path_b_dict = {row['member_id']: row for row in path_b}

    common_ancestors = set(path_a_dict.keys()) & set(path_b_dict.keys())

    if not common_ancestors:
        return None  # 没有亲缘关系

    # 找距离之和最小的共同祖先
    best = min(common_ancestors,
               key=lambda mid: path_a_dict[mid]['distance'] + path_b_dict[mid]['distance'])

    # 第四步：回溯从 A 到共同祖先、从 B 到共同祖先的路径
    route_a = _trace_route(cursor, member_id_a, best)
    route_b = _trace_route(cursor, member_id_b, best)

    return {
        'common_ancestor': path_a_dict[best]['name'],
        'common_ancestor_id': best,
        'path_a': route_a,      # A → 祖先
        'path_b': route_b,      # B → 祖先
        'total_distance': path_a_dict[best]['distance'] + path_b_dict[best]['distance'],
    }


def _trace_route(conn, from_id, to_id):
    """回溯从 from_id 到 to_id 的路径"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        WITH RECURSIVE route AS (
            SELECT m.member_id, m.name, m.member_id AS next_parent
            FROM members m WHERE m.member_id = %s
            UNION ALL
            SELECT m.member_id, m.name, fl.parent_id
            FROM route r
            JOIN family_links fl ON r.member_id = fl.child_id
            JOIN members m ON fl.child_id = m.member_id
            WHERE r.member_id != %s
        )
        SELECT DISTINCT member_id, name FROM route
    """, (from_id, to_id))
    return cursor.fetchall()