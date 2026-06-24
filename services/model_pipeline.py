"""Feed consolidated student data to the LLM and parse the structured report.

Uses a fixed 3-phase workflow:
  Phase 1 — Exploration:  Kimi queries tools to gather broad data (schools, majors, scores)
  Phase 2 — Analysis:     Kimi deep-dives into shortlisted options
  Phase 3 — Report:       Kimi generates the final structured JSON
"""

import json
import logging
import os
import re
from pathlib import Path

from openai import AsyncOpenAI

from services.security import build_secure_prompt
from services.knowledge_service import TOOLS, handle_tool_call

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1"),
    api_key=os.getenv("MOONSHOT_API_KEY"),
)


def _extract_json(raw: str) -> dict:
    raw = raw.strip()

    # 1. Direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown code fences manually
    cleaned = raw
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```\w*\s*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)

    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass

    # 3. Extract from first { to last }
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON.\nPreview: {raw[:500]}")


async def _call_with_tools(messages: list, max_rounds: int = 3) -> list:
    """Run a tool-calling loop and return the updated messages list."""
    for _ in range(max_rounds):
        response = await client.chat.completions.create(
            model=os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k"),
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=4000,
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return messages  # done with this phase

        for tc in msg.tool_calls:
            logger.info("  Tool: %s", tc.function.name)
            try:
                args = json.loads(tc.function.arguments)
                result = handle_tool_call(tc.function.name, args)
            except Exception as e:
                result = json.dumps({"error": str(e)})
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })
    return messages


async def generate_report(
    data_path: Path,
    prompt_template_path: Path,
    patterns: str = "",
) -> dict:
    """3-phase workflow: Explore → Analyze → Report."""
    data = json.loads(data_path.read_text(encoding="utf-8"))
    template = prompt_template_path.read_text(encoding="utf-8")

    # Prepare template
    if patterns:
        template = template.replace("{historical_patterns}", patterns)
    else:
        template = template.replace("{historical_patterns}\n", "")
    template = template.replace("{reference_data}\n", "")
    student_json = json.dumps(data, indent=2, ensure_ascii=False)

    system_msg = {
        "role": "system",
        "content": "你是一位专业的高考志愿填报顾问。你可以使用工具查询实时数据。"
                   "请严格按照流程回答，每个阶段完成明确的任务。",
    }

    # ── Phase 1: Exploration ──────────────────────────────────────
    logger.info("=== Phase 1: Exploration ===")
    messages = [
        system_msg,
        {
            "role": "user",
            "content": (
                f"【第一阶段：初步探索】\n"
                f"学生数据：\n{student_json}\n\n"
                f"请使用工具查询以下数据：\n"
                f"1. 该省份的录取分数线\n"
                f"2. 该分数段可报考的大学\n"
                f"3. 学生兴趣相关的专业信息\n"
                f"4. 偏好城市的大学\n\n"
                f"完成查询后，列出3-5个可能适合的专业方向及对应大学。"
            ),
        },
    ]
    messages = await _call_with_tools(messages, max_rounds=3)
    phase1_summary = next(
        (m.content for m in reversed(messages) if getattr(m, "role", None) == "assistant" and getattr(m, "content", None)),
        "",
    )

    # ── Phase 2: Deep Analysis ────────────────────────────────────
    logger.info("=== Phase 2: Deep Analysis ===")
    messages.append({
        "role": "user",
        "content": (
            "【第二阶段：深度分析】\n"
            "基于上一阶段的数据，对每个推荐方向进行深入分析：\n"
            f"1. 如果还需要补充数据，可以继续使用相关工具\n"
            f"2. 分析每个专业的：AI替代风险、就业前景、竞争热度\n"
            f"3. 给出详细的择校策略（推荐学校及理由）\n"
            f"4. 列出目标城市和就业公司\n\n"
            f"输出一个结构化的分析结果。"
        ),
    })
    messages = await _call_with_tools(messages, max_rounds=3)
    phase2_summary = next(
        (m.content for m in reversed(messages) if getattr(m, "role", None) == "assistant" and getattr(m, "content", None)),
        "",
    )

    # ── Phase 3: Final Report ─────────────────────────────────────
    logger.info("=== Phase 3: Final Report ===")
    messages.append({
        "role": "user",
        "content": (
            "【第三阶段：生成报告】\n"
            "基于以上所有分析，生成最终的 JSON 推荐报告。\n\n"
            "报告格式要求：\n"
            "{\n"
            '  "profileSummary": { "cluster": "学生类型标签", "province": "..", '
            '"score": "..", "subjectTrack": "..", "preferredCities": [...] },\n'
            '  "top": [{ "id": "专业标识", "name": "专业名", '
            '"recommendationBand": "强推荐/推荐/可选", '
            '"matchScore": 0-100, "aiRisk": "低/中/高", '
            '"outlook": "...", "competitiveness": 0-100, '
            '"summary": "...", "schoolStrategy": "...", '
            '"cities": [{"name":"..","note":".."}], '
            '"companies": [{"name":".."}], '
            '"roles": [{"id":"..","name":"..","currentDemand":"..","requirements":[".."]}], '
            '"yearPlan": {"year1":[".."],"year2":[".."],"year3":[".."],"year4":[".."]}\n'
            "  }],\n"
            '  "cautious": [...],\n'
            '  "all": 必须与 top 格式相同的完整对象数组（不是简单 ID 列表，而是完整的推荐对象）\n'
            "}\n\n"
            "只返回 JSON，不要加其他文字。确保每个 top 项都有完整的 yearPlan。all 字段必须是完整的推荐对象，不能是字符串列表。"
        ),
    })
    response = await client.chat.completions.create(
        model=os.getenv("MOONSHOT_MODEL", "moonshot-v1-32k"),
        messages=messages,
        temperature=0.5,
        max_tokens=12000,
    )
    content = response.choices[0].message.content or "{}"
    logger.info("Phase 3 response: %s chars", len(content))

    # Debug: log first and last 200 chars to diagnose parsing failures
    logger.info("Phase 3 first 200: %s", content[:200])
    logger.info("Phase 3 last 200: %s", content[-200:])

    result = _extract_json(content)

    # Safety net: fill missing required fields (marked as auto-generated)
    for field in ("top", "cautious", "all"):
        if field not in result:
            logger.warning("Kimi omitted '%s', auto-filling with empty list", field)
            result[field] = []
    if "profileSummary" not in result:
        logger.warning("Kimi omitted 'profileSummary', auto-filling")
        result["profileSummary"] = {"_auto_filled": True, "cluster": "未生成"}

    # Ensure "all" contains full objects, not strings
    if result.get("all") and isinstance(result["all"][0], str):
        logger.warning("Kimi returned strings in 'all', converting to dicts")
        by_id = {}
        for entry in result.get("top", []) + result.get("cautious", []):
            by_id[entry.get("id", "")] = entry
        result["all"] = [by_id.get(sid, {"id": sid, "name": sid, "_auto_filled": True}) for sid in result["all"]]

    return result
