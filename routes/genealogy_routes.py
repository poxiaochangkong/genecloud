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
    """获取族谱树形结构（批量查询 + 深度限制，默认3代）"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    # Parse depth parameter (default 3 generations)
    max_depth = request.args.get('depth', 3, type=int)
    max_depth = max(1, min(30, max_depth))

    conn = get_connection()
    try:
        # Permission check
        from services.permission_service import check_access
        ok, err, _ = check_access(conn, user_id, genealogy_id, 3)
        if not ok:
            return jsonify({'error': err}), 403

        cursor = conn.cursor(dictionary=True)

        # Batch query: all parent-child links for this genealogy
        cursor.execute("""
            SELECT fl.child_id, fl.parent_id, fl.relation_type
            FROM family_links fl
            JOIN members m ON fl.child_id = m.member_id
            WHERE m.genealogy_id = %s
        """, (genealogy_id,))
        all_links = cursor.fetchall()

        # Batch query: all marriages for this genealogy
        cursor.execute("""
            SELECT mar.member_id1, mar.member_id2, mar.marriage_year
            FROM marriages mar
            JOIN members m ON mar.member_id1 = m.member_id
            WHERE m.genealogy_id = %s
        """, (genealogy_id,))
        all_marriages = cursor.fetchall()

        # Batch query: all members for this genealogy
        members = find_members_by_genealogy(conn, genealogy_id)
        # find_members_by_genealogy now returns (rows, total) tuple
        if isinstance(members, tuple):
            members = members[0]

        # Build member info map
        member_map = {}
        for m in members:
            mid = m['member_id']
            member_map[mid] = {
                'member_id': mid,
                'name': m['name'],
                'gender': m['gender'],
                'birth_year': m['birth_year'],
                'death_year': m['death_year'],
                'spouse': None,
                'children': [],
                'has_more_children': False
            }

        # Build parent lookup: child_id -> [(parent_id, relation_type)]
        child_to_parents = {}
        parent_to_children = {}
        has_parents = set()
        for link in all_links:
            cid = link['child_id']
            pid = link['parent_id']
            rt = link['relation_type']
            child_to_parents.setdefault(cid, []).append((pid, rt))
            parent_to_children.setdefault(pid, []).append((cid, rt))
            has_parents.add(cid)

        # Build spouse lookup: member_id -> first spouse info
        spouse_map = {}
        for mar in all_marriages:
            id1, id2 = mar['member_id1'], mar['member_id2']
            if id1 in member_map and id2 in member_map:
                spouse_map.setdefault(id1, []).append(id2)
                spouse_map.setdefault(id2, []).append(id1)

        # Attach spouse info
        for mid, spouses in spouse_map.items():
            if mid in member_map and spouses:
                sid = spouses[0]
                s = member_map[sid]
                member_map[mid]['spouse'] = {
                    'member_id': s['member_id'],
                    'name': s['name'],
                    'gender': s['gender'],
                    'birth_year': s['birth_year'],
                    'death_year': s['death_year'],
                    'is_blood_member': s['member_id'] in has_parents
                }

        # Build tree using BFS from roots, limited to max_depth
        # Roots = members without parents AND who have direct children
        # Only members with their own family_links children records qualify as roots
        # (spouses are excluded because they have no parent-child links as parent)
        root_ids = [
            mid for mid in member_map
            if mid not in has_parents
            and parent_to_children.get(mid)
        ]

        # Build tree recursively with depth limit
        visited = set()

        def build_node(mid, depth):
            if mid in visited or mid not in member_map:
                return None
            visited.add(mid)

            node = member_map[mid]
            if depth + 1 < max_depth:
                # Get children
                children_data = parent_to_children.get(mid, [])
                # Also get children via spouse
                for sid in spouse_map.get(mid, []):
                    children_data.extend(parent_to_children.get(sid, []))

                seen_child_ids = set()
                for cid, rt in children_data:
                    if cid in seen_child_ids or cid not in member_map:
                        continue
                    seen_child_ids.add(cid)
                    child_node = build_node(cid, depth + 1)
                    if child_node:
                        node['children'].append(child_node)

            if depth + 1 >= max_depth and parent_to_children.get(mid):
                node['has_more_children'] = True

            return node

        roots = []
        for rid in root_ids:
            tree_node = build_node(rid, 0)
            if tree_node:
                roots.append(tree_node)

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
    """SQL查询2：年龄超过50岁且没有配偶的男性成员（分页）"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    page = max(1, page)
    page_size = max(1, min(200, page_size))

    conn = get_connection()
    try:
        result, error = get_old_males_without_spouse(
            conn, genealogy_id, user_id, page, page_size)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@genealogy_bp.route('/api/genealogies/<int:genealogy_id>/stats/born-before-gen-avg')
def api_born_before_gen_avg(genealogy_id):
    """SQL查询3：出生年份早于该辈分平均出生年份的成员（分页）"""
    user_id = _require_login()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    page = max(1, page)
    page_size = max(1, min(200, page_size))

    conn = get_connection()
    try:
        result, error = get_members_born_before_gen_avg(
            conn, genealogy_id, user_id, page, page_size)
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
