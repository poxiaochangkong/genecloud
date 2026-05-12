# config.py
"""
数据库和其他配置
"""

# 数据库配置
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',       # 改成你的MySQL密码
    'database': 'genealogy_db',
    'charset': 'utf8mb4',
}

# Flask 配置
SECRET_KEY = 'your-secret-key-change-in-production'
