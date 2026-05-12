# services/auth_service.py
"""
认证业务逻辑：注册、登录
"""
import hashlib
from dao.user_dao import find_user_by_username, insert_user, find_user_by_id


def _hash_password(password):
    """简单哈希密码（实验用，生产环境请用 bcrypt）"""
    return hashlib.sha256(password.encode()).hexdigest()


def register(conn, username, password, email=None):
    """
    注册新用户
    返回: (user_dict, error_message)
    """
    # 检查用户名是否已存在
    existing = find_user_by_username(conn, username)
    if existing:
        return None, "用户名已存在"

    # 检查用户名长度
    if len(username) < 2 or len(username) > 20:
        return None, "用户名长度需在2-20之间"

    # 检查密码长度
    if len(password) < 6:
        return None, "密码长度不能少于6位"

    # 创建用户
    password_hash = _hash_password(password)
    user_id = insert_user(conn, username, password_hash, email)

    return {'user_id': user_id, 'username': username}, None


def login(conn, username, password):
    """
    用户登录
    返回: (user_dict, error_message)
    """
    user = find_user_by_username(conn, username)
    if not user:
        return None, "用户名或密码错误"

    password_hash = _hash_password(password)
    if user['password_hash'] != password_hash:
        return None, "用户名或密码错误"

    # 返回用户信息（不含密码）
    return {
        'user_id': user['user_id'],
        'username': user['username'],
        'email': user['email'],
    }, None


def get_user_info(conn, user_id):
    """获取用户信息"""
    user = find_user_by_id(conn, user_id)
    if not user:
        return None, "用户不存在"
    return {
        'user_id': user['user_id'],
        'username': user['username'],
        'email': user['email'],
    }, None