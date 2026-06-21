"""Knowledge base service — selects relevant reference data per student and injects into prompt."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path("data/knowledge")

# Cache loaded data to avoid repeated file I/O
_cache = {}


def _load(name: str) -> dict:
    """Load a JSON knowledge file (cached)."""
    if name not in _cache:
        path = KNOWLEDGE_DIR / name
        if path.exists():
            _cache[name] = json.loads(path.read_text(encoding="utf-8"))
        else:
            _cache[name] = {}
            logger.warning("Knowledge file not found: %s", path)
    return _cache[name]


def get_reference_data(student_data: dict) -> str:
    """Build a compact reference-data block for the prompt, tailored to this student.

    Returns an empty string when there is no relevant data.
    """
    province = student_data.get("province", "")
    score = student_data.get("score")
    interests = student_data.get("interests", "")
    preferred_cities = student_data.get("preferredCities") or student_data.get("city", "")

    # Normalize preferred cities
    if isinstance(preferred_cities, str):
        preferred_cities = [preferred_cities]

    parts = []

    # ── 1. Admission scores for this province ─────────────────────
    scores_data = _load("admission_scores.json")
    province_data = scores_data.get("provinces", {}).get(province, {})
    if province_data and score:
        line = province_data.get("province_control_line", {})
        line_str = ""
        if line:
            line_str = "（" + "、".join(f"{k}线{v}" for k, v in line.items()) + "）"
        
        schools = province_data.get("universities", [])
        matches = []
        for s in schools:
            min_s = s.get("min_score", 0)
            if min_s and score and abs(score - min_s) <= 60:
                matches.append(f"  - {s['name']}: {min_s}分")
        
        if matches:
            sc = str(score)
            parts.append(f"### 参考分数线（{province}）{line_str}")
            parts.append(f"你的分数{sc}分，以下学校近年录取线在±60分范围内：")
            parts.extend(matches[:12])  # max 12 rows

    # ── 2. University info ───────────────────────────────────────
    uni_data = _load("universities.json")
    unis = uni_data.get("schools", [])

    # Filter: preferred cities + nearby
    target_unis = []
    if preferred_cities:
        for city in preferred_cities:
            for u in unis:
                if u.get("city") == city and u.get("name") not in target_unis:
                    target_unis.append(u)

    if target_unis:
        parts.append("\n### 偏好城市重点大学")
        for u in target_unis[:8]:
            tier = u.get("tier", "")
            dc = "双一流" if u.get("double_first_class") else ""
            tag = f"[{tier}]" if tier != "双非" else ""
            tag += f"[{dc}]" if dc else ""
            parts.append(f"  - {u['name']} {tag} {u['city']} {u.get('type','')}")

    # ── 3. Major info (only if interests mentioned) ──────────────
    maj_data = _load("majors.json")
    majors = maj_data.get("majors", [])

    if interests:
        # Find majors matching the interests text
        interest_keywords = interests.lower()
        matched = []
        for m in majors:
            name = m.get("name", "").lower()
            keywords = " ".join(m.get("keywords", []))
            field = m.get("category", "").lower()
            # Simple relevance: check if interest text contains major name parts
            for kw in name.split():
                if len(kw) >= 2 and kw in interest_keywords:
                    matched.append(m)
                    break

        # If no keyword match, show majors matching the student's subject track
        if not matched:
            track = student_data.get("subjectTrack", "")
            if "理" in track or "物" in track:
                matched = [m for m in majors if m.get("category") in ("工学", "理学", "医学")]
            elif "文" in track:
                matched = [m for m in majors if m.get("category") in ("经济学", "法学", "文学")]

        if matched:
            parts.append("\n### 相关专业信息")
            for m in matched[:5]:
                info_parts = [
                    m["name"],
                    f"AI风险:{m.get('ai_risk','?')}",
                    f"前景:{m.get('outlook','?')}",
                    f"竞争热度:{m.get('competitiveness','?')}/100",
                ]
                top = m.get("top_universities", [])
                if top:
                    info_parts.append("强校:" + ",".join(top[:4]))
                companies = m.get("target_companies", [])
                if companies:
                    info_parts.append("对口:" + ",".join(companies[:4]))
                parts.append("  - " + " | ".join(info_parts))

    result = "\n".join(parts)
    logger.info("Knowledge data generated (%d chars)", len(result))
    return result
