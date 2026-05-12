# app.py
"""
Flask 主应用入口
"""
from flask import Flask, render_template, session, redirect, url_for
from config import DATABASE_CONFIG, SECRET_KEY
from routes.auth_routes import auth_bp
from routes.genealogy_routes import genealogy_bp
from routes.member_routes import member_bp
from routes.relation_routes import relation_bp

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


if __name__ == '__main__':
    app.run(debug=True, port=5000)
