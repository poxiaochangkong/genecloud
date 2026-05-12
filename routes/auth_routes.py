# routes/auth_routes.py
"""
认证相关的路由
"""
from flask import Blueprint, request, jsonify, session
from dao.db import get_connection
from services.auth_service import register, login, get_user_info

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    """注册接口"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    conn = get_connection()
    try:
        result, error = register(
            conn,
            data.get('username', ''),
            data.get('password', ''),
            data.get('email')
        )
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 201
    finally:
        conn.close()


@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """登录接口"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    conn = get_connection()
    try:
        result, error = login(
            conn,
            data.get('username', ''),
            data.get('password', '')
        )
        if error:
            return jsonify({'error': error}), 401

        # 将用户信息存入 session
        session['user_id'] = result['user_id']
        session['username'] = result['username']
        return jsonify(result), 200
    finally:
        conn.close()


@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    """登出接口"""
    session.clear()
    return jsonify({'message': '已登出'}), 200


@auth_bp.route('/api/me')
def api_me():
    """获取当前登录用户信息"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': '未登录'}), 401

    conn = get_connection()
    try:
        result, error = get_user_info(conn, user_id)
        if error:
            return jsonify({'error': error}), 404
        return jsonify(result), 200
    finally:
        conn.close()