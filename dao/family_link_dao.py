# dao/family_link_dao.py
"""
血缘关系的数据访问层（包含递归CTE查询）
这是整个项目最核心的 DAO
"""
from collections import deque


def find_parents(conn, child_id):
    """
    查找某人的所有父母（包括通过婚姻推断：已知父亲则其配偶为母亲，反之亦然）
    返回结果中 source 字段表示：'direct' 直接血缘，'inferred' 通过婚姻推断
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        -- 直接血缘父母
        SELECT fl.parent_id AS member_id, m.name, fl.relation_type, 'direct' AS source
        FROM family_links fl
        JOIN members m ON fl.parent_id = m.member_id
        WHERE fl.child_id = %s

        UNION

        -- 通过婚姻推断另一方父母
        SELECT spouse.member_id, spouse.name, inferred.relation_type, 'inferred' AS source
        FROM family_links fl
        JOIN marriages mar ON fl.parent_id = mar.member_id1 OR fl.parent_id = mar.member_id2
        JOIN members spouse ON spouse.member_id =
            CASE WHEN fl.parent_id = mar.member_id1 THEN mar.member_id2 ELSE mar.member_id1 END
        CROSS JOIN (
            SELECT 'mother' AS relation_type
            UNION ALL SELECT 'father'
        ) inferred
        WHERE fl.child_id = %s
          -- 推断规则：已知父亲 → 推论母亲；已知母亲 → 推论父亲
          AND ((fl.relation_type = 'father' AND inferred.relation_type = 'mother')
               OR (fl.relation_type = 'mother' AND inferred.relation_type = 'father'))
          -- 匹配性别：推论的父亲必须为男，推论的母亲必须为女
          AND ((inferred.relation_type = 'father' AND spouse.gender = 'M')
               OR (inferred.relation_type = 'mother' AND spouse.gender = 'F'))
          -- 排除已在血缘关系中存在的
          AND spouse.member_id NOT IN (
              SELECT parent_id FROM family_links WHERE child_id = %s
          )
    """, (child_id, child_id, child_id))
    return cursor.fetchall()


def find_children(conn, parent_id):
    """查找某人的所有子女（包括通过婚姻推断：即配偶的子女也是自己的子女）"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT fl.child_id AS member_id, m.name,
               CASE WHEN fl.parent_id = %s THEN 'direct' ELSE 'via_spouse' END AS source
        FROM family_links fl
        JOIN members m ON fl.child_id = m.member_id
        WHERE fl.parent_id IN (
            -- 本人
            SELECT %s
            UNION
            -- 配偶
            SELECT CASE WHEN mar.member_id1 = %s THEN mar.member_id2 ELSE mar.member_id1 END
            FROM marriages mar
            WHERE mar.member_id1 = %s OR mar.member_id2 = %s
        )
    """, (parent_id, parent_id, parent_id, parent_id, parent_id))
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
    查询某成员的所有祖先（递归向上追溯，支持婚姻推断）
    返回从父母（第1代）到最古老祖先的完整链路，包括通过婚姻关联的祖先
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        WITH RECURSIVE ancestors AS (
            -- 锚点：从给定成员开始，generation=0（本人，不纳入最终结果）
            SELECT m.member_id, m.name, m.gender, m.birth_year,
                   fl.parent_id, fl.relation_type, 0 AS generation,
                   CAST(m.member_id AS CHAR(5000)) AS visited
            FROM members m
            LEFT JOIN family_links fl ON m.member_id = fl.child_id
            WHERE m.member_id = %s

            UNION ALL

            -- 血缘向上：child → parent
            SELECT m.member_id, m.name, m.gender, m.birth_year,
                   fl.parent_id, fl.relation_type, a.generation + 1,
                   CONCAT(a.visited, ',', m.member_id)
            FROM ancestors a
            JOIN members m ON a.parent_id = m.member_id
            LEFT JOIN family_links fl ON m.member_id = fl.child_id
            WHERE a.parent_id IS NOT NULL
              AND FIND_IN_SET(CAST(m.member_id AS CHAR), a.visited) = 0
              AND a.generation < 50

            UNION ALL

            -- 婚姻横向：成员→配偶（配偶视为关系上的上一代，嫁入/入赘场景）
            SELECT spouse.member_id, spouse.name, spouse.gender, spouse.birth_year,
                   fl.parent_id, fl.relation_type, a.generation + 1,
                   CONCAT(a.visited, ',', spouse.member_id)
            FROM ancestors a
            JOIN marriages mar ON a.member_id = mar.member_id1 OR a.member_id = mar.member_id2
            JOIN members spouse ON spouse.member_id =
                CASE WHEN a.member_id = mar.member_id1 THEN mar.member_id2 ELSE mar.member_id1 END
            LEFT JOIN family_links fl ON spouse.member_id = fl.child_id
            WHERE FIND_IN_SET(CAST(spouse.member_id AS CHAR), a.visited) = 0
              AND a.generation < 50
        )
        SELECT member_id, name, gender, birth_year,
               MIN(relation_type) AS relation_type, MIN(generation) AS generation
        FROM ancestors WHERE generation > 0
        GROUP BY member_id, name, gender, birth_year
        ORDER BY generation
    """, (member_id,))
    return cursor.fetchall()


def find_all_descendants(conn, member_id):
    """
    查询某成员的所有后代（递归向下展开，支持婚姻推断）
    包括配偶的子女也视为自己的后代
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        WITH RECURSIVE descendants AS (
            -- 锚点：从给定成员开始，generation=1（本人）
            SELECT m.member_id, m.name, m.gender, m.birth_year,
                   1 AS generation,
                   CAST(m.member_id AS CHAR(5000)) AS visited
            FROM members m
            WHERE m.member_id = %s

            UNION ALL

            -- 血缘向下：parent → child
            SELECT m.member_id, m.name, m.gender, m.birth_year,
                   d.generation + 1,
                   CONCAT(d.visited, ',', m.member_id)
            FROM descendants d
            JOIN family_links fl ON d.member_id = fl.parent_id
            JOIN members m ON fl.child_id = m.member_id
            WHERE FIND_IN_SET(CAST(m.member_id AS CHAR), d.visited) = 0
              AND d.generation < 50

            UNION ALL

            -- 婚姻横向：当前后代成员的配偶也作为同代后人（嫁入/入赘场景）
            SELECT spouse.member_id, spouse.name, spouse.gender, spouse.birth_year,
                   d.generation,
                   CONCAT(d.visited, ',', spouse.member_id)
            FROM descendants d
            JOIN marriages mar ON d.member_id = mar.member_id1 OR d.member_id = mar.member_id2
            JOIN members spouse ON spouse.member_id =
                CASE WHEN d.member_id = mar.member_id1 THEN mar.member_id2 ELSE mar.member_id1 END
            WHERE FIND_IN_SET(CAST(spouse.member_id AS CHAR), d.visited) = 0
              AND d.generation < 50
        )
        SELECT member_id, name, gender, birth_year, MIN(generation) AS generation
        FROM descendants
        GROUP BY member_id, name, gender, birth_year
        ORDER BY generation
    """, (member_id,))
    return cursor.fetchall()


def find_kinship_path(conn, member_id_a, member_id_b):
    """
    查询两人之间的亲缘链路（支持血缘+婚姻混合路径）
    使用递归CTE分别从A和B向上/横向展开，找到最近共同祖先(LCA)
    FIND_IN_SET 用于去重防止婚姻边导致的循环
    """
    cursor = conn.cursor(dictionary=True)

    # 第一步：获取从 A 可达的所有成员及距离（血缘 + 婚姻）
    cursor.execute("""
        WITH RECURSIVE path_a AS (
            SELECT m.member_id, m.name, 0 AS distance,
                   CAST(m.member_id AS CHAR(5000)) AS visited
            FROM members m WHERE m.member_id = %s
            UNION ALL
            -- 血缘向上：child → parent
            SELECT m.member_id, m.name, pa.distance + 1,
                   CONCAT(pa.visited, ',', m.member_id)
            FROM path_a pa
            JOIN family_links fl ON pa.member_id = fl.child_id
            JOIN members m ON fl.parent_id = m.member_id
            WHERE FIND_IN_SET(CAST(m.member_id AS CHAR), pa.visited) = 0
              AND pa.distance < 40
            UNION ALL
            -- 婚姻横向：member → spouse
            SELECT m.member_id, m.name, pa.distance + 1,
                   CONCAT(pa.visited, ',', m.member_id)
            FROM path_a pa
            JOIN marriages mar ON pa.member_id = mar.member_id1 OR pa.member_id = mar.member_id2
            JOIN members m ON m.member_id =
                CASE WHEN pa.member_id = mar.member_id1 THEN mar.member_id2 ELSE mar.member_id1 END
            WHERE FIND_IN_SET(CAST(m.member_id AS CHAR), pa.visited) = 0
              AND pa.distance < 40
        )
        SELECT member_id, name, MIN(distance) AS distance
        FROM path_a GROUP BY member_id, name
    """, (member_id_a,))
    path_a = cursor.fetchall()

    # 第二步：获取从 B 可达的所有成员及距离
    cursor.execute("""
        WITH RECURSIVE path_b AS (
            SELECT m.member_id, m.name, 0 AS distance,
                   CAST(m.member_id AS CHAR(5000)) AS visited
            FROM members m WHERE m.member_id = %s
            UNION ALL
            SELECT m.member_id, m.name, pb.distance + 1,
                   CONCAT(pb.visited, ',', m.member_id)
            FROM path_b pb
            JOIN family_links fl ON pb.member_id = fl.child_id
            JOIN members m ON fl.parent_id = m.member_id
            WHERE FIND_IN_SET(CAST(m.member_id AS CHAR), pb.visited) = 0
              AND pb.distance < 40
            UNION ALL
            SELECT m.member_id, m.name, pb.distance + 1,
                   CONCAT(pb.visited, ',', m.member_id)
            FROM path_b pb
            JOIN marriages mar ON pb.member_id = mar.member_id1 OR pb.member_id = mar.member_id2
            JOIN members m ON m.member_id =
                CASE WHEN pb.member_id = mar.member_id1 THEN mar.member_id2 ELSE mar.member_id1 END
            WHERE FIND_IN_SET(CAST(m.member_id AS CHAR), pb.visited) = 0
              AND pb.distance < 40
        )
        SELECT member_id, name, MIN(distance) AS distance
        FROM path_b GROUP BY member_id, name
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
    route_a = _trace_route(conn, member_id_a, best)
    route_b = _trace_route(conn, member_id_b, best)

    return {
        'common_ancestor': path_a_dict[best]['name'],
        'common_ancestor_id': best,
        'path_a': route_a,      # A → 共同祖先
        'path_b': route_b,      # B → 共同祖先
        'total_distance': path_a_dict[best]['distance'] + path_b_dict[best]['distance'],
    }


def _trace_route(conn, from_id, to_id):
    """
    回溯从 from_id 到 to_id 的最短路径（支持血缘+婚姻混合路径）
    在 Python 中构建统一邻接图，用 BFS 找最短链路
    """
    if from_id == to_id:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT member_id, name FROM members WHERE member_id = %s",
            (from_id,)
        )
        row = cursor.fetchone()
        return [{'member_id': from_id, 'name': row['name'], 'depth': 0}] if row else []

    cursor = conn.cursor(dictionary=True)

    # 加载同一族谱中所有血缘边和婚姻边（通过 from_id 所在族谱限定范围）
    cursor.execute(
        "SELECT genealogy_id FROM members WHERE member_id = %s", (from_id,)
    )
    row = cursor.fetchone()
    if not row:
        return []
    gid = row['genealogy_id']

    # 血缘边：child → parent
    cursor.execute("""
        SELECT fl.child_id AS member_id, fl.parent_id AS neighbor_id
        FROM family_links fl
        JOIN members m ON fl.child_id = m.member_id
        WHERE m.genealogy_id = %s
    """, (gid,))
    family_edges = cursor.fetchall()

    # 婚姻边：双向 member ↔ spouse
    cursor.execute("""
        SELECT member_id1 AS member_id, member_id2 AS neighbor_id
        FROM marriages mar
        JOIN members m ON mar.member_id1 = m.member_id
        WHERE m.genealogy_id = %s
        UNION
        SELECT member_id2, member_id1
        FROM marriages mar
        JOIN members m ON mar.member_id2 = m.member_id
        WHERE m.genealogy_id = %s
    """, (gid, gid))
    spouse_edges = cursor.fetchall()

    # 构建邻接映射: member_id -> [neighbor_ids]
    adj_map = {}
    for edge in family_edges:
        adj_map.setdefault(edge['member_id'], []).append(edge['neighbor_id'])
    for edge in spouse_edges:
        adj_map.setdefault(edge['member_id'], []).append(edge['neighbor_id'])

    # BFS 寻找 from_id → to_id 的最短路径
    queue = deque([(from_id, [from_id])])
    visited = {from_id}

    while queue:
        current, path = queue.popleft()
        for neighbor in adj_map.get(current, []):
            if neighbor == to_id:
                full_path = path + [neighbor]
                placeholders = ','.join(['%s'] * len(full_path))
                cursor.execute(
                    f"SELECT member_id, name FROM members WHERE member_id IN ({placeholders})",
                    tuple(full_path)
                )
                name_map = {r['member_id']: r['name'] for r in cursor.fetchall()}
                return [{'member_id': mid, 'name': name_map.get(mid, '?'), 'depth': i}
                        for i, mid in enumerate(full_path)]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return []  # 未找到路径
