# services/member_service.py
"""
成员业务逻辑
"""
from dao.member_dao import (
    find_member_by_id, search_by_name,
    find_members_by_genealogy, insert_member,
    update_member, delete_member
)
from dao.genealogy_dao import find_genealogy_by_id


def _check_access(conn, user_id, genealogy_id):
    """检查用户是否有权操作该族谱"""
    genealogy = find_genealogy_by_id(conn, genealogy_id)
    if not genealogy:
        return False, "族谱不存在"
    if genealogy['created_by'] != user_id:
        return False, "无权操作该族谱"
    return True, None


def list_members(conn, genealogy_id, user_id):
    """列出族谱所有成员"""
    ok, err = _check_access(conn, user_id, genealogy_id)
    if not ok:
        return [], err

    members = find_members_by_genealogy(conn, genealogy_id)
    return members, None


def get_member_detail(conn, member_id, user_id):
    """获取成员详情"""
    member = find_member_by_id(conn, member_id)
    if not member:
        return None, "成员不存在"

    ok, err = _check_access(conn, user_id, member['genealogy_id'])
    if not ok:
        return None, err

    return member, None


def search_members(conn, genealogy_id, keyword, user_id):
    """模糊搜索成员"""
    ok, err = _check_access(conn, user_id, genealogy_id)
    if not ok:
        return [], err

    results = search_by_name(conn, genealogy_id, keyword)
    return results, None


def create_member(conn, genealogy_id, name, gender, birth_year,
                  death_year, bio, user_id):
    """创建新成员"""
    ok, err = _check_access(conn, user_id, genealogy_id)
    if not ok:
        return None, err

    if not name or not name.strip():
        return None, "姓名不能为空"
    if gender not in ('M', 'F'):
        return None, "性别必须为 M 或 F"
    if birth_year and (birth_year < 1 or birth_year > 2100):
        return None, "出生年份不合理"
    if death_year and birth_year and death_year < birth_year:
        return None, "死亡年份不能早于出生年份"

    member_id = insert_member(conn, genealogy_id, name.strip(),
                               gender, birth_year, death_year, bio)
    return {'member_id': member_id}, None


def modify_member(conn, member_id, name, gender, birth_year,
                  death_year, bio, user_id):
    """修改成员信息"""
    member = find_member_by_id(conn, member_id)
    if not member:
        return None, "成员不存在"

    ok, err = _check_access(conn, user_id, member['genealogy_id'])
    if not ok:
        return None, err

    update_member(conn, member_id, name, gender, birth_year, death_year, bio)
    return {'member_id': member_id}, None


def remove_member(conn, member_id, user_id):
    """删除成员"""
    member = find_member_by_id(conn, member_id)
    if not member:
        return None, "成员不存在"

    ok, err = _check_access(conn, user_id, member['genealogy_id'])
    if not ok:
        return None, err

    delete_member(conn, member_id)
    return {'message': '删除成功'}, None