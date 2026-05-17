# routes/member_routes.py
"""
成员相关的路由
"""
from flask import Blueprint, request, jsonify, session
from dao.db import get_connection
from services.member_service import (
    list_members, get_member_detail, search_members,
    create_member, modify_member, remove_member
)

member_bp = Blueprint('members', __name__)


def _get_user_id():
    return session.get('user_id')


@member_bp.route('/api/genealogies/<int:genealogy_id>/members')
def api_list_members(genealogy_id):
    """列出族谱成员（支持分页：?page=1&page_size=50）"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    # Parse pagination params
    page = request.args.get('page', type=int)
    page_size = request.args.get('page_size', 50, type=int)
    # Clamp page_size to reasonable range
    page_size = max(1, min(200, page_size))

    conn = get_connection()
    try:
        if page is not None:
            result, error = list_members(conn, genealogy_id, user_id, page, page_size)
        else:
            result, error = list_members(conn, genealogy_id, user_id)
        if error:
            return jsonify({'error': error}), 403
        return jsonify(result), 200
    finally:
        conn.close()


@member_bp.route('/api/members/<int:member_id>')
def api_get_member(member_id):
    """获取成员详情"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = get_member_detail(conn, member_id, user_id)
        if error:
            return jsonify({'error': error}), 404
        return jsonify(result), 200
    finally:
        conn.close()


@member_bp.route('/api/genealogies/<int:genealogy_id>/members/search')
def api_search_members(genealogy_id):
    """搜索成员"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    keyword = request.args.get('keyword', '')
    conn = get_connection()
    try:
        result, error = search_members(conn, genealogy_id, keyword, user_id)
        if error:
            return jsonify({'error': error}), 403
        return jsonify(result), 200
    finally:
        conn.close()


@member_bp.route('/api/genealogies/<int:genealogy_id>/members', methods=['POST'])
def api_create_member(genealogy_id):
    """创建成员"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    data = request.get_json()
    conn = get_connection()
    try:
        result, error = create_member(
            conn, genealogy_id,
            data.get('name', ''),
            data.get('gender', 'M'),
            data.get('birth_year'),
            data.get('death_year'),
            data.get('bio'),
            user_id
        )
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 201
    finally:
        conn.close()


@member_bp.route('/api/members/<int:member_id>', methods=['PUT'])
def api_update_member(member_id):
    """更新成员"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    data = request.get_json()
    conn = get_connection()
    try:
        result, error = modify_member(
            conn, member_id,
            data.get('name', ''),
            data.get('gender', 'M'),
            data.get('birth_year'),
            data.get('death_year'),
            data.get('bio'),
            user_id
        )
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@member_bp.route('/api/members/<int:member_id>', methods=['DELETE'])
def api_delete_member(member_id):
    """删除成员"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = remove_member(conn, member_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()