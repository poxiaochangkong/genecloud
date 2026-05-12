# services/member_service.py
"""
成员业务逻辑
"""
import datetime
from dao.member_dao import (
    find_member_by_id, search_by_name,
    find_members_by_genealogy, insert_member,
    update_member, delete_member
)
from services.permission_service import check_access


def list_members(conn, genealogy_id, user_id):
    """列出族谱所有成员"""
    ok, err = check_access(conn, user_id, genealogy_id, 3)
    if not ok:
        return [], err

    members = find_members_by_genealogy(conn, genealogy_id)
    return members, None


def get_member_detail(conn, member_id, user_id):
    """获取成员详情"""
    member = find_member_by_id(conn, member_id)
    if not member:
        return None, "成员不存在"

    ok, err = check_access(conn, user_id, member['genealogy_id'], 3)
    if not ok:
        return None, err

    return member, None


def search_members(conn, genealogy_id, keyword, user_id):
    """模糊搜索成员"""
    ok, err = check_access(conn, user_id, genealogy_id, 3)
    if not ok:
        return [], err

    results = search_by_name(conn, genealogy_id, keyword)
    return results, None


def create_member(conn, genealogy_id, name, gender, birth_year,
                  death_year, bio, user_id):
    """创建新成员"""
    ok, err = check_access(conn, user_id, genealogy_id, 3)
    if not ok:
        return None, err

    if not name or not name.strip():
        return None, "姓名不能为空"
    if gender not in ('M', 'F'):
        return None, "性别必须为 M 或 F"
    current_year = datetime.datetime.now().year
    if birth_year and (birth_year < 1 or birth_year > current_year):
        return None, f"出生年份必须在 1 ~ {current_year} 之间"
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

    ok, err = check_access(conn, user_id, member['genealogy_id'], 3)
    if not ok:
        return None, err

    update_member(conn, member_id, name, gender, birth_year, death_year, bio)
    return {'member_id': member_id}, None


def remove_member(conn, member_id, user_id):
    """删除成员"""
    member = find_member_by_id(conn, member_id)
    if not member:
        return None, "成员不存在"

    ok, err = check_access(conn, user_id, member['genealogy_id'], 3)
    if not ok:
        return None, err

    delete_member(conn, member_id)
    return {'message': '删除成功'}, None