# models/user.py
"""
用户数据模型，对应 users 表
"""


class User:
    def __init__(self, user_id, username, password_hash, email=None, created_at=None):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.created_at = created_at

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'created_at': str(self.created_at) if self.created_at else None,
        }