"""Knowledge base tools — callable by Kimi via function calling."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path("data/knowledge")
_cache = {}


def _load(name: str) -> dict:
    if name not in _cache:
        path = KNOWLEDGE_DIR / name
        if path.exists():
            _cache[name] = json.loads(path.read_text(encoding="utf-8"))
        else:
            _cache[name] = {}
    return _cache[name]


# ── Tool definitions (sent to Kimi as function schema) ────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_admission_scores",
            "description": "查询某省份某分数段内可报考的大学及其历年录取分数线",
            "parameters": {
                "type": "object",
                "properties": {
                    "province": {"type": "string", "description": "省份名称, 如 广东"},
                    "score": {"type": "number", "description": "高考分数"},
                    "range": {"type": "number", "description": "分数浮动范围（默认60分）"},
                },
                "required": ["province", "score"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_university_info",
            "description": "查询大学的基本信息：层次（985/211）、城市、类型",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称（可选）"},
                    "name": {"type": "string", "description": "大学名称（可选）"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_major_details",
            "description": "查询专业的详细信息：前景、AI风险、强校、对口企业、技能要求",
            "parameters": {
                "type": "object",
                "properties": {
                    "interest_keywords": {
                        "type": "string",
                        "description": "兴趣关键词, 如 计算机、编程、AI",
                    },
                },
                "required": ["interest_keywords"],
            },
        },
    },
]


# ── Tool execution handlers ────────────────────────────────────────

def handle_tool_call(name: str, args: dict) -> str:
    """Execute a tool and return a JSON string result."""
    handlers = {
        "get_admission_scores": _handle_admission_scores,
        "get_university_info": _handle_university_info,
        "get_major_details": _handle_major_details,
    }
    handler = handlers.get(name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = handler(**args)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _handle_admission_scores(province: str, score: float, range: float = 60) -> dict:
    scores_data = _load("admission_scores.json")
    province_data = scores_data.get("provinces", {}).get(province, {})
    if not province_data:
        return {"matches": [], "message": f"暂无{province}的数据"}

    line = province_data.get("province_control_line", {})
    schools = province_data.get("universities", [])
    matches = []
    for s in schools:
        min_s = s.get("min_score", 0)
        if min_s and abs(score - min_s) <= range:
            matches.append({
                "name": s["name"],
                "min_score": min_s,
                "min_rank": s.get("min_rank"),
                "gap": round(score - min_s, 1),
            })
    matches.sort(key=lambda x: abs(x["gap"]))

    return {
        "province": province,
        "your_score": score,
        "control_line": line,
        "matches": matches,
        "total_in_database": len(schools),
    }


def _handle_university_info(city: str = None, name: str = None) -> dict:
    uni_data = _load("universities.json")
    unis = uni_data.get("schools", [])
    results = []

    for u in unis:
        if name and name in u["name"]:
            results.append(u)
        elif city and u.get("city") == city:
            results.append(u)

    if not results:
        return {"message": "未找到匹配的大学", "results": []}
    return {"results": results[:10]}


def _handle_major_details(interest_keywords: str) -> dict:
    maj_data = _load("majors.json")
    majors = maj_data.get("majors", [])
    keywords = interest_keywords.lower()
    results = []

    for m in majors:
        name = m["name"].lower()
        # Score relevance: how many characters of the interest match the major name
        score = sum(1 for kw in name.split() if len(kw) >= 2 and kw in keywords)
        if score > 0:
            results.append((score, m))
    
    # If no keyword match, return all majors with categories matching tech
    if not results:
        for m in majors:
            results.append((0, m))

    results.sort(key=lambda x: -x[0])
    return {
        "majors": [r[1] for r in results[:5]],
        "total_available": len(majors),
    }
