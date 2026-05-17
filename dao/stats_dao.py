# dao/stats_dao.py
"""
统计分析的数据访问层（PPT要求的3个SQL查询）

辈分计算策略（修复配偶辈分问题）：
1. 以父系（relation_type='father'）为轴线递归计算辈分
2. 通过 marriages 表将配偶分配到与伴侣相同的辈分
3. 无血缘、无婚姻关系的孤立成员归为第1代
"""

# ---- 公共CTE片段（辈分计算） ----
# 用法：在SQL中插入此片段，并传入 genealogy_id 参数
_GEN_TREE_CTE = """
WITH RECURSIVE gen_blood AS (
    -- 第1步：沿父系轴线递归，计算血系成员辈分
    -- 根节点 = 有子女作为父亲、但自己不是任何人的子女
    SELECT m.member_id, m.name, m.gender, m.birth_year, m.death_year,
           1 AS generation
    FROM members m
    WHERE m.genealogy_id = %s
      AND m.member_id IN (SELECT parent_id FROM family_links WHERE relation_type = 'father')
      AND m.member_id NOT IN (SELECT child_id FROM family_links WHERE child_id IS NOT NULL)

    UNION ALL

    -- 递归：父亲的子女（含儿子、女儿）
    SELECT m.member_id, m.name, m.gender, m.birth_year, m.death_year,
           gb.generation + 1
    FROM gen_blood gb
    JOIN family_links fl ON gb.member_id = fl.parent_id AND fl.relation_type = 'father'
    JOIN members m ON fl.child_id = m.member_id
),
gen_blood_dedup AS (
    -- 去重：每个血系成员只保留最小辈分
    SELECT member_id, name, gender, birth_year, death_year,
           MIN(generation) AS generation
    FROM gen_blood
    GROUP BY member_id, name, gender, birth_year, death_year
),
gen_with_spouses AS (
    -- 第2步：配偶获得与伴侣相同的辈分
    SELECT member_id, name, gender, birth_year, death_year, generation
    FROM gen_blood_dedup

    UNION

    SELECT m.member_id, m.name, m.gender, m.birth_year, m.death_year, g.generation
    FROM gen_blood_dedup g
    JOIN marriages mar ON (g.member_id = mar.member_id1 OR g.member_id = mar.member_id2)
    JOIN members m ON m.member_id = CASE
        WHEN mar.member_id1 = g.member_id THEN mar.member_id2
        ELSE mar.member_id1
    END
    WHERE m.genealogy_id = %s
),
gen_tree AS (
    -- 第3步：最终去重（血系辈分优先）+ 孤立成员归第1代
    SELECT member_id, name, gender, birth_year, death_year,
           MIN(generation) AS generation
    FROM (
        SELECT member_id, name, gender, birth_year, death_year, generation
        FROM gen_with_spouses
        UNION ALL
        SELECT m.member_id, m.name, m.gender, m.birth_year, m.death_year, 1
        FROM members m
        WHERE m.genealogy_id = %s
          AND NOT EXISTS (
              SELECT 1 FROM gen_with_spouses gws
              WHERE gws.member_id = m.member_id
          )
    ) all_src
    GROUP BY member_id, name, gender, birth_year, death_year
)
"""


def find_avg_lifespan_by_generation(conn, genealogy_id):
    """
    SQL查询1：统计某家族中平均寿命最长的一代人（辈分）
    使用递归CTE计算辈分，再按辈分聚合AVG(寿命)
    """
    cursor = conn.cursor(dictionary=True)
    sql = _GEN_TREE_CTE + """
        SELECT generation,
               COUNT(*) AS member_count,
               ROUND(AVG(death_year - birth_year), 1) AS avg_lifespan
        FROM gen_tree
        WHERE death_year IS NOT NULL AND birth_year IS NOT NULL
        GROUP BY generation
        ORDER BY avg_lifespan DESC
        LIMIT 1
    """
    cursor.execute(sql, (genealogy_id, genealogy_id, genealogy_id))
    return cursor.fetchone()


def find_old_males_without_spouse(conn, genealogy_id):
    """
    SQL查询2：查询所有年龄超过50岁、且没有配偶的男性成员
    - 在世：年龄 = 当前年份 - 出生年份
    - 已故：年龄 = 逝世年份 - 出生年份（即寿命）
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.member_id, m.name, m.gender, m.birth_year, m.death_year,
               CASE WHEN m.death_year IS NOT NULL
                    THEN m.death_year - m.birth_year
                    ELSE YEAR(CURDATE()) - m.birth_year
               END AS age,
               CASE WHEN m.death_year IS NOT NULL
                    THEN '已故'
                    ELSE '在世'
               END AS status
        FROM members m
        WHERE m.genealogy_id = %s
          AND m.gender = 'M'
          AND m.birth_year IS NOT NULL
          AND CASE WHEN m.death_year IS NOT NULL
                   THEN m.death_year - m.birth_year
                   ELSE YEAR(CURDATE()) - m.birth_year
              END > 50
          AND m.member_id NOT IN (
              SELECT member_id1 FROM marriages
              WHERE member_id1 IS NOT NULL
              UNION
              SELECT member_id2 FROM marriages
              WHERE member_id2 IS NOT NULL
          )
        ORDER BY m.birth_year
    """, (genealogy_id,))
    return cursor.fetchall()


def find_members_born_before_gen_avg(conn, genealogy_id):
    """
    SQL查询3：找出家族中"出生年份"早于该辈分（代）平均出生年份的所有成员
    使用父系轴线递归CTE计算辈分（配偶与伴侣同辈），再与辈分平均值比较
    """
    cursor = conn.cursor(dictionary=True)
    sql = _GEN_TREE_CTE + """,
        gen_avg AS (
            SELECT generation, ROUND(AVG(birth_year), 1) AS avg_birth_year
            FROM gen_tree
            WHERE birth_year IS NOT NULL
            GROUP BY generation
        )
        SELECT gt.member_id, gt.name, gt.gender, gt.generation,
               gt.birth_year, ga.avg_birth_year,
               ROUND(ga.avg_birth_year - gt.birth_year, 1) AS years_before_avg
        FROM gen_tree gt
        JOIN gen_avg ga ON gt.generation = ga.generation
        WHERE gt.birth_year IS NOT NULL
          AND gt.birth_year < ga.avg_birth_year
        ORDER BY gt.generation, gt.birth_year
    """
    cursor.execute(sql, (genealogy_id, genealogy_id, genealogy_id))
    return cursor.fetchall()


def find_generation_details(conn, genealogy_id):
    """
    辅助查询：列出每代的统计信息（代数、人数、平均出生年、平均寿命）
    """
    cursor = conn.cursor(dictionary=True)
    sql = _GEN_TREE_CTE + """
        SELECT generation,
               COUNT(*) AS member_count,
               ROUND(AVG(birth_year), 1) AS avg_birth_year,
               ROUND(AVG(death_year - birth_year), 1) AS avg_lifespan
        FROM gen_tree
        WHERE birth_year IS NOT NULL
        GROUP BY generation
        ORDER BY generation
    """
    cursor.execute(sql, (genealogy_id, genealogy_id, genealogy_id))
    return cursor.fetchall()