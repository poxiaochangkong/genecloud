# services/relation_service.py
"""
关系查询业务逻辑（递归CTE查询）
"""
from dao.family_link_dao import (
    find_parents, find_children, insert_family_link,
    find_all_ancestors, find_all_descendants, find_kinship_path
)
from dao.marriage_dao import find_spouses, insert_marriage, delete_marriage
from dao.member_dao import find_member_by_id
from services.permission_service import check_access


def get_parents(conn, member_id, user_id):
    """获取某人的父母"""
    member = find_member_by_id(conn, member_id)
    if not member:
        return None, "成员不存在"

    ok, err = check_access(conn, user_id, member['genealogy_id'], 3)
    if not ok:
        return None, err

    parents = find_parents(conn, member_id)
    return parents, None


def get_children(conn, member_id, user_id):
    """获取某人的子女"""
    member = find_member_by_id(conn, member_id)
    if not member:
        return None, "成员不存在"

    ok, err = check_access(conn, user_id, member['genealogy_id'], 3)
    if not ok:
        return None, err

    children = find_children(conn, member_id)
    return children, None


def add_parent_link(conn, child_id, parent_id, relation_type, user_id):
    """建立亲子关系"""
    if child_id == parent_id:
        return None, "不能将自己设为自己的父母"

    valid_types = ('father', 'mother')
    if relation_type not in valid_types:
        return None, f"relation_type 必须是 {valid_types} 之一"

    child = find_member_by_id(conn, child_id)
    parent = find_member_by_id(conn, parent_id)

    if not child or not parent:
        return None, "成员不存在"

    # 性别与关系类型匹配
    if relation_type == 'father' and parent['gender'] != 'M':
        return None, "父亲的性别必须为男"
    if relation_type == 'mother' and parent['gender'] != 'F':
        return None, "母亲的性别必须为女"

    # 两人必须在同一个族谱
    if child['genealogy_id'] != parent['genealogy_id']:
        return None, "父母和子女必须在同一个族谱"

    # 防止循环引用：检查 child 是否是 parent 的祖先
    ancestors = find_all_ancestors(conn, parent_id)
    if any(a['member_id'] == child_id for a in ancestors):
        return None, "不能将祖先设为子女，会造成循环引用"

    ok, err = check_access(conn, user_id, child['genealogy_id'], 3)
    if not ok:
        return None, err

    insert_family_link(conn, child_id, parent_id, relation_type)
    return {'message': '关系建立成功'}, None


def query_ancestors(conn, member_id, user_id):
    """查询某人的所有祖先（递归CTE）"""
    member = find_member_by_id(conn, member_id)
    if not member:
        return None, "成员不存在"

    ok, err = check_access(conn, user_id, member['genealogy_id'], 3)
    if not ok:
        return None, err

    ancestors = find_all_ancestors(conn, member_id)
    return ancestors, None


def query_descendants(conn, member_id, user_id):
    """查询某人的所有后代（递归CTE）"""
    member = find_member_by_id(conn, member_id)
    if not member:
        return None, "成员不存在"

    ok, err = check_access(conn, user_id, member['genealogy_id'], 3)
    if not ok:
        return None, err

    descendants = find_all_descendants(conn, member_id)
    return descendants, None


def get_spouses(conn, member_id, user_id):
    """获取某人的配偶"""
    member = find_member_by_id(conn, member_id)
    if not member:
        return None, "成员不存在"
    ok, err = check_access(conn, user_id, member['genealogy_id'], 3)
    if not ok:
        return None, err
    spouses = find_spouses(conn, member_id)
    return spouses, None


def add_marriage(conn, member_id1, member_id2, marriage_year, user_id):
    """建立夫妻关系"""
    if member_id1 == member_id2:
        return None, "不能与自己结婚"

    m1 = find_member_by_id(conn, member_id1)
    m2 = find_member_by_id(conn, member_id2)
    if not m1 or not m2:
        return None, "成员不存在"
    if m1['genealogy_id'] != m2['genealogy_id']:
        return None, "两人必须在同一个族谱"

    ok, err = check_access(conn, user_id, m1['genealogy_id'], 2)
    if not ok:
        return None, err

    marriage_id = insert_marriage(conn, member_id1, member_id2, marriage_year)
    return {'marriage_id': marriage_id, 'message': '婚姻关系建立成功'}, None


def remove_marriage(conn, marriage_id, user_id):
    """解除婚姻关系"""
    from dao.marriage_dao import find_marriage_by_id
    mar = find_marriage_by_id(conn, marriage_id)
    if not mar:
        return None, "婚姻关系不存在"

    # 检查任意一方所在的族谱权限
    m1 = find_member_by_id(conn, mar['member_id1'])
    if m1:
        ok, err = check_access(conn, user_id, m1['genealogy_id'], 2)
        if not ok:
            return None, err

    delete_marriage(conn, marriage_id)
    return {'message': '婚姻关系已解除'}, None


def query_kinship(conn, member_id_a, member_id_b, user_id):
    """查询两人之间的亲缘链路"""
    a = find_member_by_id(conn, member_id_a)
    b = find_member_by_id(conn, member_id_b)

    if not a or not b:
        return None, "成员不存在"

    # 两人必须在同一个族谱
    if a['genealogy_id'] != b['genealogy_id']:
        return None, "两人不在同一个族谱"

    ok, err = check_access(conn, user_id, a['genealogy_id'], 3)
    if not ok:
        return None, err

    path = find_kinship_path(conn, member_id_a, member_id_b)
    if not path:
        return None, "两人之间没有亲缘关系"

    return path, None