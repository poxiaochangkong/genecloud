# routes/relation_routes.py
"""
关系查询相关的路由
"""
from flask import Blueprint, request, jsonify, session
from dao.db import get_connection
from services.relation_service import (
    get_parents, get_children, add_parent_link,
    query_ancestors, query_descendants, query_kinship,
    get_spouses, add_marriage, remove_marriage
)

relation_bp = Blueprint('relations', __name__)


def _get_user_id():
    return session.get('user_id')


@relation_bp.route('/api/members/<int:member_id>/parents')
def api_get_parents(member_id):
    """获取某人的父母"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = get_parents(conn, member_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@relation_bp.route('/api/members/<int:member_id>/children')
def api_get_children(member_id):
    """获取某人的子女"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = get_children(conn, member_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@relation_bp.route('/api/relations/link', methods=['POST'])
def api_add_link():
    """建立亲子关系"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    data = request.get_json()
    conn = get_connection()
    try:
        result, error = add_parent_link(
            conn,
            data['child_id'],
            data['parent_id'],
            data['relation_type'],
            user_id
        )
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 201
    finally:
        conn.close()


@relation_bp.route('/api/members/<int:member_id>/ancestors')
def api_ancestors(member_id):
    """查询所有祖先（递归CTE）"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = query_ancestors(conn, member_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@relation_bp.route('/api/members/<int:member_id>/descendants')
def api_descendants(member_id):
    """查询所有后代（递归CTE）"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = query_descendants(conn, member_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@relation_bp.route('/api/members/<int:member_id>/spouses')
def api_get_spouses(member_id):
    """获取某人的配偶"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = get_spouses(conn, member_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@relation_bp.route('/api/relations/marriage', methods=['POST'])
def api_add_marriage():
    """建立夫妻关系"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    data = request.get_json()
    conn = get_connection()
    try:
        result, error = add_marriage(
            conn,
            data['member_id1'],
            data['member_id2'],
            data.get('marriage_year'),
            user_id
        )
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 201
    finally:
        conn.close()


@relation_bp.route('/api/relations/marriage/<int:marriage_id>', methods=['DELETE'])
def api_remove_marriage(marriage_id):
    """解除婚姻关系"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = remove_marriage(conn, marriage_id, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


@relation_bp.route('/api/relations/kinship')
def api_kinship():
    """查询两人之间的亲缘链路"""
    user_id = _get_user_id()
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    member_a = request.args.get('member_a', type=int)
    member_b = request.args.get('member_b', type=int)

    if not member_a or not member_b:
        return jsonify({'error': '请提供两个成员ID'}), 400

    conn = get_connection()
    try:
        result, error = query_kinship(conn, member_a, member_b, user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()