# models/member.py
"""
成员数据模型，对应 members 表
"""
from datetime import datetime


class Member:
    def __init__(self, member_id, genealogy_id, name, gender,
                 birth_year=None, death_year=None, bio=None):
        self.member_id = member_id
        self.genealogy_id = genealogy_id
        self.name = name
        self.gender = gender          # 'M' = 男, 'F' = 女
        self.birth_year = birth_year
        self.death_year = death_year
        self.bio = bio

    def to_dict(self):
        return {
            'member_id': self.member_id,
            'genealogy_id': self.genealogy_id,
            'name': self.name,
            'gender': self.gender,
            'birth_year': self.birth_year,
            'death_year': self.death_year,
            'bio': self.bio,
        }

    def age(self):
        """计算年龄"""
        if self.birth_year is None:
            return None
        end_year = self.death_year if self.death_year else datetime.now().year
        return end_year - self.birth_year

    def is_alive(self):
        """是否在世"""
        return self.death_year is None