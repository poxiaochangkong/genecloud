# app.py
"""
Flask 主应用入口
"""
from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from config import DATABASE_CONFIG, SECRET_KEY
from routes.auth_routes import auth_bp
from routes.genealogy_routes import genealogy_bp
from routes.member_routes import member_bp
from routes.relation_routes import relation_bp
from dao.db import get_connection
from services.permission_service import get_current_admin, transfer_admin

app = Flask(__name__)
app.secret_key = SECRET_KEY

# 注册所有蓝图（路由模块）
app.register_blueprint(auth_bp)
app.register_blueprint(genealogy_bp)
app.register_blueprint(member_bp)
app.register_blueprint(relation_bp)


@app.route('/')
def index():
    """首页"""
    if 'user_id' in session:
        return render_template('dashboard.html')
    return render_template('login.html')


@app.route('/genealogies')
def genealogies_page():
    """族谱列表页"""
    return render_template('genealogy_list.html')


@app.route('/genealogies/<int:genealogy_id>')
def genealogy_detail_page(genealogy_id):
    """族谱详情页"""
    return render_template('genealogy_detail.html', genealogy_id=genealogy_id)


@app.route('/members/<int:member_id>')
def member_detail_page(member_id):
    """成员详情页"""
    return render_template('member_detail.html', member_id=member_id)



# ---------- 管理员 API ----------

@app.route('/api/admin/current')
def api_current_admin():
    """获取当前管理员信息"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': '未登录'}), 401
    conn = get_connection()
    try:
        admin = get_current_admin(conn)
        if not admin:
            return jsonify({'error': '无管理员'}), 404
        return jsonify(admin), 200
    finally:
        conn.close()


@app.route('/api/admin/transfer', methods=['POST'])
def api_transfer_admin():
    """转让管理员"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': '未登录'}), 401
    data = request.get_json()
    if not data or not data.get('username'):
        return jsonify({'error': '请提供目标用户名'}), 400
    conn = get_connection()
    try:
        result, error = transfer_admin(conn, data['username'], user_id)
        if error:
            return jsonify({'error': error}), 400
        return jsonify(result), 200
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
