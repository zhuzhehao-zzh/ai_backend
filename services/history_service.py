"""Historical pattern analysis for prompt enrichment."""

import logging
from collections import Counter

from services.database import pool

logger = logging.getLogger(__name__)


async def get_pattern_summary() -> str:
    """Compute aggregated insights from past consultations.

    Returns a short text block to inject into the prompt, or empty string
    when there is insufficient data (< 5 consultations).
    """
    if pool is None:
        return ""

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 1. Total consultations
            await cur.execute("SELECT COUNT(*) FROM requests")
            total = (await cur.fetchone())[0]
            if total < 5:
                return ""

            # 2. Average rating per major
            await cur.execute("""
                SELECT
                    JSON_UNQUOTE(JSON_EXTRACT(r.report, CONCAT('$.top[', j.idx, '].name'))) AS major,
                    AVG(f.rating) AS avg_rating,
                    COUNT(*) AS times
                FROM responses r
                JOIN feedback f ON f.response_id = r.response_id
                JOIN (
                    SELECT 0 AS idx UNION ALL SELECT 1 UNION ALL SELECT 2
                    UNION ALL SELECT 3 UNION ALL SELECT 4
                ) j
                WHERE JSON_EXTRACT(r.report, CONCAT('$.top[', j.idx, '].name')) IS NOT NULL
                GROUP BY major
                HAVING times >= 2
                ORDER BY avg_rating DESC
                LIMIT 5
            """)
            major_ratings = await cur.fetchall()

            # 3. Most common score bands
            await cur.execute("""
                SELECT
                    FLOOR(JSON_EXTRACT(student_data, '$.score') / 50) * 50 AS band,
                    COUNT(*) AS cnt
                FROM requests
                WHERE JSON_EXTRACT(student_data, '$.score') IS NOT NULL
                GROUP BY band
                ORDER BY cnt DESC
                LIMIT 5
            """)
            score_bands = await cur.fetchall()

            # 4. Most popular cities
            await cur.execute("""
                SELECT
                    JSON_UNQUOTE(JSON_EXTRACT(
                        r.report, CONCAT('$.top[', j.idx, '].cities[0].name')
                    )) AS city,
                    COUNT(*) AS cnt
                FROM responses r
                JOIN (
                    SELECT 0 AS idx UNION ALL SELECT 1 UNION ALL SELECT 2
                ) j
                WHERE JSON_EXTRACT(r.report, CONCAT('$.top[', j.idx, '].cities[0].name')) IS NOT NULL
                GROUP BY city
                ORDER BY cnt DESC
                LIMIT 5
            """)
            cities = await cur.fetchall()

    # Build summary text
    parts = [f"基于{total}次历史咨询的统计："]
    
    if major_ratings:
        parts.append("高满意度专业推荐：")
        for m in major_ratings[:3]:
            parts.append(f"  - {m[0]}（平均评分{m[1]:.1f}/5，推荐{m[2]}次）")
    
    if score_bands:
        parts.append("常见分数段分布：")
        for b in score_bands[:3]:
            parts.append(f"  - {b[0]}-{b[0]+50}分：{b[1]}人")

    if cities:
        top_cities = [c[0] for c in cities[:3]]
        parts.append(f"推荐最多的城市：{'、'.join(top_cities)}")

    return "\n".join(parts)
