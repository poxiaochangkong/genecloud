# services/genealogy_service.py
"""
族谱业务逻辑
"""
from dao.genealogy_dao import (
    find_genealogies_by_user, find_genealogy_by_id,
    insert_genealogy, delete_genealogy
)
from services.permission_service import check_access, grant


def list_genealogies(conn, user_id):
    """获取用户可见的所有族谱"""
    genealogies = find_genealogies_by_user(conn, user_id)
    return genealogies, None


def create_genealogy(conn, name, surname, user_id):
    """创建新族谱，并自动给创建者 owner 权限"""
    if not name or not name.strip():
        return None, "族谱名称不能为空"
    if not surname or not surname.strip():
        return None, "姓氏不能为空"

    genealogy_id = insert_genealogy(conn, name.strip(), surname.strip(), user_id)
    # 自动插入 owner 权限记录
    from dao.permission_dao import grant_permission
    grant_permission(conn, user_id, genealogy_id, 'owner')
    return {'genealogy_id': genealogy_id, 'name': name}, None


def get_genealogy_detail(conn, genealogy_id, user_id):
    """获取族谱详情（含权限校验）"""
    genealogy = find_genealogy_by_id(conn, genealogy_id)
    if not genealogy:
        return None, "族谱不存在"

    ok, err = check_access(conn, user_id, genealogy_id, 3)
    if not ok:
        return None, err

    return genealogy, None


def remove_genealogy(conn, genealogy_id, user_id):
    """删除族谱（需要1级或2级权限）"""
    genealogy = find_genealogy_by_id(conn, genealogy_id)
    if not genealogy:
        return None, "族谱不存在"

    ok, err = check_access(conn, user_id, genealogy_id, 2)
    if not ok:
        return None, err

    delete_genealogy(conn, genealogy_id)
    return {'message': '族谱已删除'}, None
