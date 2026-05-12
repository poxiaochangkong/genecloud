# dao/db.py
"""
数据库连接管理
"""
import mysql.connector
from config import DATABASE_CONFIG


def get_connection():
    """获取数据库连接"""
    return mysql.connector.connect(**DATABASE_CONFIG)