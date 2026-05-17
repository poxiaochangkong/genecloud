# routes/genealogy_routes.py
"""
族谱相关的路由
"""
from flask import Blueprint, request, jsonify, session
from dao.db import get_connection
from dao.member_dao import find_members_by_genealogy
from dao.family_link_dao import find_parents
from dao.marriage_dao import find_spouses
from services.genealogy_service import (
    list_genealogies, create_genealogy, get_genealogy_detail,
    remove_genealogy
)
from services.stats_service import (
    get_dashboard_stats, get_avg_lifespan_by_generation,
    get_old_males_without_spouse, get_members_born_before_gen_avg,
    get_generation_details
)
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
    """获取族谱树形结构（血系主干 + 配偶并排）"""
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

        # Build member info map and record has_parents in a single pass
        member_map = {}
        has_parents = set()  # member_ids that have parent links
        for m in members:
            mid = m['member_id']
            member_map[mid] = {
                'member_id': mid,
                'name': m['name'],
                'gender': m['gender'],
                'birth_year': m['birth_year'],
                'death_year': m['death_year'],
                'spouse': None,
                'children': []
            }

        # Build parent-child relationships (single pass, avoid duplicate find_parents)
        for m in members:
            mid = m['member_id']
            parents = find_parents(conn, mid)
            if parents:
                has_parents.add(mid)
                # Attach child to father first; fall back to mother
                father = next((p for p in parents if p['relation_type'] == 'father'), None)
                if father and father['member_id'] in member_map:
                    member_map[father['member_id']]['children'].append(member_map[mid])
                else:
                    mother = next((p for p in parents if p['relation_type'] == 'mother'), None)
                    if mother and mother['member_id'] in member_map:
                        member_map[mother['member_id']]['children'].append(member_map[mid])

        # Attach spouse info to each member via marriages table
        for m in members:
            mid = m['member_id']
            spouses = find_spouses(conn, mid)
            if spouses:
                # Use the first spouse as the primary spouse displayed in tree
                s = spouses[0]
                member_map[mid]['spouse'] = {
                    'member_id': s['member_id'],
                    'name': s['name'],
                    'gender': s['gender'],
                    'birth_year': s['birth_year'],
                    'death_year': s['death_year'],
                    'marriage_year': s.get('marriage_year'),
                    'is_blood_member': s['member_id'] in has_parents
                }

        # Find roots: members without parents who have children (blood-line ancestors)
        # Isolated spouses (married-in, no parents, no children) are excluded
        roots = []
        for m in members:
            mid = m['member_id']
            if mid not in has_parents:
                node = member_map[mid]
                if node['children']:
                    roots.append(node)
                else:
                    # Also include childless root members who are NOT someone's spouse
                    # (e.g. a single person with no relations at all)
                    is_spouse_of_someone = False
                    for m2 in members:
                        if m2['member_id'] != mid:
                            s = member_map[m2['member_id']].get('spouse')
                            if s and s['member_id'] == mid:
                                is_spouse_of_someone = True
                                break
                    if not is_spouse_of_someone:
                        roots.append(node)

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


# ============================================
# PPT要求的SQL查询API端点
# ============================================

@genealogy_bp.route('/api/genealogies/<int:genealogy_id>/stats/lifespan-by-gen')
def api_lifespan_by_gen(genealogy_id):
    """SQL查询1：统计平均寿命最长的一代人"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = get_avg_lifespan_by_generation(conn, genealogy_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@genealogy_bp.route('/api/genealogies/<int:genealogy_id>/stats/old-males-no-spouse')
def api_old_males_no_spouse(genealogy_id):
    """SQL查询2：年龄超过50岁且没有配偶的男性成员"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = get_old_males_without_spouse(conn, genealogy_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@genealogy_bp.route('/api/genealogies/<int:genealogy_id>/stats/born-before-gen-avg')
def api_born_before_gen_avg(genealogy_id):
    """SQL查询3：出生年份早于该辈分平均出生年份的成员"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = get_members_born_before_gen_avg(conn, genealogy_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@genealogy_bp.route('/api/genealogies/<int:genealogy_id>/stats/generation-details')
def api_generation_details(genealogy_id):
    """辅助查询：各代统计信息"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = get_generation_details(conn, genealogy_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()
