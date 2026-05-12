# models/family_link.py
"""
血缘关系数据模型，对应 family_links 表
"""


class FamilyLink:
    def __init__(self, link_id, child_id, parent_id, relation_type):
        self.link_id = link_id
        self.child_id = child_id
        self.parent_id = parent_id
        self.relation_type = relation_type    # 'father' 或 'mother'

    def to_dict(self):
        return {
            'link_id': self.link_id,
            'child_id': self.child_id,
            'parent_id': self.parent_id,
            'relation_type': self.relation_type,
        }