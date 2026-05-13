# services/relation_service.py
"""
关系查询业务逻辑（递归CTE查询）
"""
from dao.family_link_dao import (
    find_parents, find_children, insert_family_link,
    find_all_ancestors, find_all_descendants, find_kinship_path
)
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

    # 两人必须在同一个族谱
    if child['genealogy_id'] != parent['genealogy_id']:
        return None, "父母和子女必须在同一个族谱"

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