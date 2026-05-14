# services/permission_service.py
"""
权限业务逻辑：校验、赋予、撤销
"""
from dao.permission_dao import (
    get_user_role, get_genealogy_permissions,
    grant_permission, revoke_permission, find_user_by_username
)
from dao.user_dao import (
    find_user_by_id, find_all_users, find_genealogies_by_creator,
    count_genealogies_by_user, delete_user_by_id
)
from dao.genealogy_dao import delete_genealogy


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

    # 管理员是全局身份，不能通过族谱权限撤销
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT is_admin FROM users WHERE user_id = %s", (target_user_id,))
    target_user = cursor.fetchone()
    if target_user and target_user['is_admin']:
        return None, "不能撤销管理员的权限"

    # 不能撤销比自己更高权限的人
    operator_role = get_user_role(conn, operator_id, genealogy_id)
    target_role = get_user_role(conn, target_user_id, genealogy_id)
    if operator_role == 'owner' and target_role in ('admin', 'owner'):
        return None, "Owner 不能撤销 admin 或 owner 的权限"

    revoke_permission(conn, target_user_id, genealogy_id)
    return {'message': '权限已撤销'}, None


def get_current_admin(conn):
    """获取当前管理员信息"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id, username, email FROM users WHERE is_admin = 1")
    return cursor.fetchone()


def transfer_admin(conn, target_username, operator_id):
    """
    管理员转让：保证有且仅有1个管理员
    用数据库事务保证原子性
    """
    # 检查操作者是否是管理员
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT is_admin FROM users WHERE user_id = %s", (operator_id,))
    operator = cursor.fetchone()
    if not operator or not operator['is_admin']:
        return None, "只有管理员可以转让管理员身份"

    # 查找目标用户
    target = find_user_by_username(conn, target_username)
    if not target:
        return None, "目标用户不存在"

    target_id = target['user_id']
    if target_id == operator_id:
        return None, "不能转让给自己"

    # 检查目标是否已是管理员
    cursor.execute("SELECT is_admin FROM users WHERE user_id = %s", (target_id,))
    target_user = cursor.fetchone()
    if target_user and target_user['is_admin']:
        return None, "目标用户已经是管理员"

    # 事务：旧admin设为0，新admin设为1
    try:
        cursor.execute("UPDATE users SET is_admin = 0 WHERE user_id = %s", (operator_id,))
        cursor.execute("UPDATE users SET is_admin = 1 WHERE user_id = %s", (target_id,))
        conn.commit()
        return {'message': f'管理员已转让给 {target_username}'}, None
    except Exception as e:
        conn.rollback()
        return None, f"转让失败: {str(e)}"


def delete_user_cascade(conn, target_user_id, operator_id):
    """
    删除用户及其创建的所有族谱（级联删除成员、关系、协作）
    只有 admin 可以操作，且不能删除自己或另一位 admin
    返回: (result, error_message)
    """
    # 检查操作者是否是 admin
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT is_admin FROM users WHERE user_id = %s", (operator_id,))
    operator = cursor.fetchone()
    if not operator or not operator['is_admin']:
        return None, "只有管理员可以删除用户"

    # 检查目标用户是否存在
    target = find_user_by_id(conn, target_user_id)
    if not target:
        return None, "目标用户不存在"

    # 不能删除自己
    if target_user_id == operator_id:
        return None, "不能删除自己"

    # 不能删除另一位管理员
    if target.get('is_admin'):
        return None, "不能删除管理员用户"

    # 查询该用户创建的所有族谱
    genealogies = find_genealogies_by_creator(conn, target_user_id)
    genealogy_count = len(genealogies)

    try:
        # 逐个删除该用户创建的族谱（delete_genealogy 会级联删除成员/关系/协作）
        for g in genealogies:
            delete_genealogy(conn, g['genealogy_id'])

        # 删除该用户参与的其他协作记录（非 owner 的 collaboration）
        cursor.execute(
            "DELETE FROM collaborations WHERE user_id = %s",
            (target_user_id,)
        )

        # 最后删除用户本身
        deleted = delete_user_by_id(conn, target_user_id)
        if deleted == 0:
            conn.rollback()
            return None, "删除用户失败"

        conn.commit()
        return {
            'message': f'用户 {target["username"]} 已删除',
            'deleted_genealogies': genealogy_count,
            'deleted_user_id': target_user_id
        }, None
    except Exception as e:
        conn.rollback()
        return None, f"删除失败: {str(e)}"


def preview_delete_user(conn, target_user_id, operator_id):
    """
    预览删除用户的影响（不实际执行删除）
    返回用户信息、其创建的族谱列表等
    """
    # 检查操作者是否是 admin
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT is_admin FROM users WHERE user_id = %s", (operator_id,))
    operator = cursor.fetchone()
    if not operator or not operator['is_admin']:
        return None, "只有管理员可以删除用户"

    target = find_user_by_id(conn, target_user_id)
    if not target:
        return None, "目标用户不存在"

    if target_user_id == operator_id:
        return None, "不能删除自己"

    if target.get('is_admin'):
        return None, "不能删除管理员用户"

    genealogies = find_genealogies_by_creator(conn, target_user_id)

    return {
        'user_id': target['user_id'],
        'username': target['username'],
        'email': target.get('email'),
        'genealogy_count': len(genealogies),
        'genealogies': [{'id': g['genealogy_id'], 'name': g['name']} for g in genealogies]
    }, None