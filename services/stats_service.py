# services/stats_service.py
"""
统计分析业务逻辑
"""
from dao.member_dao import find_members_by_genealogy
from dao.genealogy_dao import find_genealogy_by_id
from dao.stats_dao import (
    find_avg_lifespan_by_generation,
    find_old_males_without_spouse,
    find_members_born_before_gen_avg,
    find_generation_details
)
from services.permission_service import check_access


def get_dashboard_stats(conn, genealogy_id, user_id):
    """获取 Dashboard 统计数据"""
    genealogy = find_genealogy_by_id(conn, genealogy_id)
    if not genealogy:
        return None, "族谱不存在"

    ok, err, _ = check_access(conn, user_id, genealogy_id, 3)
    if not ok:
        return None, err

    result = find_members_by_genealogy(conn, genealogy_id)
    # Handle both old (list) and new (tuple) return formats
    members = result[0] if isinstance(result, tuple) else result

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


def get_avg_lifespan_by_generation(conn, genealogy_id, user_id):
    """统计某家族中平均寿命最长的一代人"""
    ok, err, _ = check_access(conn, user_id, genealogy_id, 3)
    if not ok:
        return None, err

    result = find_avg_lifespan_by_generation(conn, genealogy_id)
    if not result:
        return None, "没有足够的数据计算各代平均寿命"
    return result, None


def get_old_males_without_spouse(conn, genealogy_id, user_id, page=1, page_size=50):
    """查询所有年龄超过50岁且没有配偶的男性成员（分页）"""
    ok, err, _ = check_access(conn, user_id, genealogy_id, 3)
    if not ok:
        return None, err

    results, total = find_old_males_without_spouse(conn, genealogy_id, page, page_size)
    return {'data': results, 'total': total, 'page': page, 'page_size': page_size}, None


def get_members_born_before_gen_avg(conn, genealogy_id, user_id, page=1, page_size=50):
    """找出出生年份早于该辈分平均出生年份的所有成员（分页）"""
    ok, err, _ = check_access(conn, user_id, genealogy_id, 3)
    if not ok:
        return None, err

    results, total = find_members_born_before_gen_avg(conn, genealogy_id, page, page_size)
    return {'data': results, 'total': total, 'page': page, 'page_size': page_size}, None


def get_generation_details(conn, genealogy_id, user_id):
    """获取各代统计信息"""
    ok, err, _ = check_access(conn, user_id, genealogy_id, 3)
    if not ok:
        return None, err

    results = find_generation_details(conn, genealogy_id)
    return results, None