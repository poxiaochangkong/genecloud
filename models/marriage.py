# models/marriage.py
"""
婚姻关系数据模型，对应 marriages 表
"""


class Marriage:
    def __init__(self, marriage_id, member_id1, member_id2,
                 marriage_year=None, divorce_year=None):
        self.marriage_id = marriage_id
        self.member_id1 = member_id1
        self.member_id2 = member_id2
        self.marriage_year = marriage_year
        self.divorce_year = divorce_year

    def to_dict(self):
        return {
            'marriage_id': self.marriage_id,
            'member_id1': self.member_id1,
            'member_id2': self.member_id2,
            'marriage_year': self.marriage_year,
            'divorce_year': self.divorce_year,
        }