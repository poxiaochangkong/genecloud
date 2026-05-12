# routes/genealogy_routes.py
"""
族谱相关的路由
"""
from flask import Blueprint, request, jsonify, session
from dao.db import get_connection
from services.genealogy_service import (
    list_genealogies, create_genealogy, get_genealogy_detail
)
from services.stats_service import get_dashboard_stats

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