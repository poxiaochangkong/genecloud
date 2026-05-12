# models/genealogy.py
"""
族谱数据模型，对应 genealogies 表
"""


class Genealogy:
    def __init__(self, genealogy_id, name, surname, created_by, created_at=None):
        self.genealogy_id = genealogy_id
        self.name = name
        self.surname = surname
        self.created_by = created_by
        self.created_at = created_at

    def to_dict(self):
        return {
            'genealogy_id': self.genealogy_id,
            'name': self.name,
            'surname': self.surname,
            'created_by': self.created_by,
            'created_at': str(self.created_at) if self.created_at else None,
        }