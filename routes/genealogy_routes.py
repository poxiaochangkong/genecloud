# routes/genealogy_routes.py
"""
族谱相关的路由
"""
from flask import Blueprint, request, jsonify, session
from dao.db import get_connection
from dao.member_dao import find_members_by_genealogy
from dao.family_link_dao import find_parents
from services.genealogy_service import (
    list_genealogies, create_genealogy, get_genealogy_detail,
    remove_genealogy
)
from services.stats_service import get_dashboard_stats
from services.permission_service import list_permissions, grant, revoke

genealogy_bp = Blueprint('genealogies', __name__)


def _require_login():
    """检查是否登录"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return user_id


@genealogy_bp.route('/api/genealogies')
def api_list_genealogies():
    """获取所有族谱"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = list_genealogies(conn, user_id)
        if error:
            return jsonify({'error': error}), 500
        return jsonify(result), 200
    finally:
        conn.close()


@genealogy_bp.route('/api/genealogies', methods=['POST'])
def api_create_genealogy():
    """创建族谱"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    data = request.get_json()
    conn = get_connection()
    try:
        result, error = create_genealogy(
            conn,
            data.get('name', ''),
            data.get('surname', ''),
            user_id
        )
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 201
    finally:
        conn.close()


@genealogy_bp.route('/api/genealogies/<int:genealogy_id>')
def api_get_genealogy(genealogy_id):
    """获取族谱详情"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = get_genealogy_detail(conn, genealogy_id, user_id)
        if error:
            return jsonify({'error': error}), 404
        return jsonify(result), 200
    finally:
        conn.close()


@genealogy_bp.route('/api/genealogies/<int:genealogy_id>', methods=['DELETE'])
def api_delete_genealogy(genealogy_id):
    """删除族谱"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = remove_genealogy(conn, genealogy_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@genealogy_bp.route('/api/genealogies/<int:genealogy_id>/stats')
def api_genealogy_stats(genealogy_id):
    """获取族谱统计数据"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = get_dashboard_stats(conn, genealogy_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@genealogy_bp.route('/api/genealogies/<int:genealogy_id>/tree')
def api_genealogy_tree(genealogy_id):
    """获取族谱树形结构"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        # 权限校验
        from services.permission_service import check_access
        ok, err = check_access(conn, user_id, genealogy_id, 3)
        if not ok:
            return jsonify({'error': err}), 403

        # 获取所有成员
        members = find_members_by_genealogy(conn, genealogy_id)

        # 获取所有父子关系
        member_map = {}
        children_map = {}
        for m in members:
            mid = m['member_id']
            member_map[mid] = {
                'member_id': mid,
                'name': m['name'],
                'gender': m['gender'],
                'birth_year': m['birth_year'],
                'death_year': m['death_year'],
                'children': []
            }
            children_map[mid] = []

        # 填充父子关系
        for m in members:
            parents = find_parents(conn, m['member_id'])
            if not parents:
                # 没有父母 → 顶层节点候选
                children_map[None].append(m['member_id']) if None in children_map else children_map.setdefault(None, [m['member_id']])
            else:
                for p in parents:
                    pid = p['parent_id']
                    if pid in member_map:
                        member_map[pid]['children'].append(member_map[m['member_id']])

        # 找根节点（没有父母的人）
        roots = []
        for m in members:
            parents = find_parents(conn, m['member_id'])
            if not parents:
                roots.append(member_map[m['member_id']])

        return jsonify(roots), 200
    finally:
        conn.close()


@genealogy_bp.route('/api/genealogies/<int:genealogy_id>/permissions')
def api_list_permissions(genealogy_id):
    """查看族谱权限列表"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = list_permissions(conn, genealogy_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@genealogy_bp.route('/api/genealogies/<int:genealogy_id>/permissions', methods=['POST'])
def api_grant_permission(genealogy_id):
    """赋予权限"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    data = request.get_json()
    conn = get_connection()
    try:
        result, error = grant(
            conn, genealogy_id,
            data.get('username', ''),
            data.get('role', 'editor'),
            user_id
        )
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@genealogy_bp.route('/api/genealogies/<int:genealogy_id>/permissions/<int:target_user_id>', methods=['DELETE'])
def api_revoke_permission(genealogy_id, target_user_id):
    """撤销权限"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = revoke(conn, genealogy_id, target_user_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()
