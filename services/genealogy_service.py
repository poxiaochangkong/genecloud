# services/genealogy_service.py
"""
族谱业务逻辑
"""
from dao.genealogy_dao import (
    find_genealogies_by_user, find_genealogy_by_id,
    insert_genealogy, delete_genealogy
)
from dao.user_dao import find_user_by_id


def list_genealogies(conn, user_id):
    """获取用户可见的所有族谱"""
    genealogies = find_genealogies_by_user(conn, user_id)
    return genealogies, None


def create_genealogy(conn, name, surname, user_id):
    """创建新族谱"""
    if not name or not name.strip():
        return None, "族谱名称不能为空"
    if not surname or not surname.strip():
        return None, "姓氏不能为空"

    genealogy_id = insert_genealogy(conn, name.strip(), surname.strip(), user_id)
    return {'genealogy_id': genealogy_id, 'name': name}, None


def get_genealogy_detail(conn, genealogy_id, user_id):
    """获取族谱详情（含权限校验）"""
    genealogy = find_genealogy_by_id(conn, genealogy_id)
    if not genealogy:
        return None, "族谱不存在"

    # 权限校验：只有创建者或协作者可以查看
    if genealogy['created_by'] != user_id:
        # TODO: 检查 collaborations 表
        pass

    return genealogy, None