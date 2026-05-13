# services/stats_service.py
"""
统计分析业务逻辑
"""
from dao.member_dao import find_members_by_genealogy
from dao.genealogy_dao import find_genealogy_by_id
from services.permission_service import check_access


def get_dashboard_stats(conn, genealogy_id, user_id):
    """获取 Dashboard 统计数据"""
    genealogy = find_genealogy_by_id(conn, genealogy_id)
    if not genealogy:
        return None, "族谱不存在"

    ok, err = check_access(conn, user_id, genealogy_id, 3)
    if not ok:
        return None, err

    members = find_members_by_genealogy(conn, genealogy_id)

    total = len(members)
    male_count = sum(1 for m in members if m['gender'] == 'M')
    female_count = sum(1 for m in members if m['gender'] == 'F')

    # 计算平均寿命
    lifespans = []
    for m in members:
        if m['birth_year'] and m['death_year']:
            lifespans.append(m['death_year'] - m['birth_year'])

    avg_lifespan = sum(lifespans) / len(lifespans) if lifespans else 0

    return {
        'genealogy_name': genealogy['name'],
        'total_members': total,
        'male_count': male_count,
        'female_count': female_count,
        'male_ratio': round(male_count / total * 100, 1) if total > 0 else 0,
        'female_ratio': round(female_count / total * 100, 1) if total > 0 else 0,
        'avg_lifespan': round(avg_lifespan, 1),
        'members_with_lifespan': len(lifespans),
    }, None