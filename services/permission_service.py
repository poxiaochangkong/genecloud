# services/permission_service.py
"""
权限业务逻辑：校验、赋予、撤销
"""
from dao.permission_dao import (
    get_user_role, get_genealogy_permissions,
    grant_permission, revoke_permission, find_user_by_username
)


# 权限级别映射
ROLE_LEVEL = {'admin': 1, 'owner': 2, 'editor': 3}


def check_access(conn, user_id, genealogy_id, required_level):
    """
    检查用户是否有足够权限
    required_level: 1=admin, 2=owner(含admin), 3=editor(含owner和admin)
    返回: (ok, error_message)
    """
    role = get_user_role(conn, user_id, genealogy_id)
    if not role:
        return False, "无权操作该族谱"
    level = ROLE_LEVEL.get(role, 0)
    if level > required_level:
        return False, f"权限不足，需要{required_level}级或更高权限"
    return True, None


def list_permissions(conn, genealogy_id, operator_id):
    """查看某族谱的权限列表"""
    ok, err = check_access(conn, operator_id, genealogy_id, 2)
    if not ok:
        return None, err
    return get_genealogy_permissions(conn, genealogy_id), None


def grant(conn, genealogy_id, username, role, operator_id):
    """赋予权限"""
    # 操作者必须是 owner 或 admin
    ok, err = check_access(conn, operator_id, genealogy_id, 2)
    if not ok:
        return None, err

    # owner 不能赋予比自己更高的权限（不能赋 admin 或 owner）
    operator_role = get_user_role(conn, operator_id, genealogy_id)
    if operator_role == 'owner' and role in ('admin', 'owner'):
        return None, "Owner 只能赋予 3级(editor) 权限"

    if role not in ('admin', 'owner', 'editor'):
        return None, "无效的权限级别"

    target = find_user_by_username(conn, username)
    if not target:
        return None, "用户不存在"

    grant_permission(conn, target['user_id'], genealogy_id, role)
    return {'message': f'已赋予 {username} {role} 权限'}, None


def revoke(conn, genealogy_id, target_user_id, operator_id):
    """撤销权限"""
    ok, err = check_access(conn, operator_id, genealogy_id, 2)
    if not ok:
        return None, err

    # 不能撤销比自己更高权限的人
    operator_role = get_user_role(conn, operator_id, genealogy_id)
    target_role = get_user_role(conn, target_user_id, genealogy_id)
    if operator_role == 'owner' and target_role in ('admin', 'owner'):
        return None, "Owner 不能撤销 admin 或 owner 的权限"

    revoke_permission(conn, target_user_id, genealogy_id)
    return {'message': '权限已撤销'}, None