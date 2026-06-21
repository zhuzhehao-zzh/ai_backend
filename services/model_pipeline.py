"""Feed consolidated student data to the LLM and parse the structured report."""

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

MAX_TOOL_ROUNDS = 5  # prevent infinite tool-calling loops


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not extract valid JSON.\nPreview: {raw[:500]}")


async def generate_report(
    data_path: Path,
    prompt_template_path: Path,
    patterns: str = "",
) -> dict:
    """Call Kimi with tool access — Kimi queries our knowledge base as needed."""
    data = json.loads(data_path.read_text(encoding="utf-8"))
    template = prompt_template_path.read_text(encoding="utf-8")

    # Inject patterns, remove reference_data placeholder
    if patterns:
        template = template.replace("{historical_patterns}", patterns)
    else:
        template = template.replace("{historical_patterns}\n", "")
    template = template.replace("{reference_data}\n", "")

    # Build prompt with student data and tool instructions
    prompt = build_secure_prompt(template, json.dumps(data, indent=2, ensure_ascii=False))

    messages = [
        {
            "role": "system",
            "content": "你是一位专业的高考志愿填报顾问。你可以使用工具查询实时数据。"
                       "请先调用工具获取所需数据（分数线、大学信息、专业详情），"
                       "然后基于真实数据给出推荐。最后返回 JSON 格式的报告。",
        },
        {"role": "user", "content": prompt},
    ]

    logger.info("Starting function-calling loop for %s", data_path.name)

    for _round in range(MAX_TOOL_ROUNDS):
        response = await client.chat.completions.create(
            model=os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k"),
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=8000,
        )

        msg = response.choices[0].message

        # No tool calls → final answer
        if not msg.tool_calls:
            logger.info("Final response received (%s chars)", len(msg.content or ""))
            return _extract_json(msg.content or "{}")

        # Execute each tool call and append results
        messages.append(msg)
        for tc in msg.tool_calls:
            logger.info("Tool call: %s(%s)", tc.function.name, tc.function.arguments[:100])
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

    # Fallback: if Kimi still wants to call tools after max rounds, force a response
    logger.warning("Max tool rounds reached, forcing response")
    messages.append({
        "role": "user",
        "content": "请基于你已经获取的数据，直接返回最终的 JSON 推荐报告。",
    })
    response = await client.chat.completions.create(
        model=os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k"),
        messages=messages,
        temperature=0.7,
        max_tokens=8000,
    )
    return _extract_json(response.choices[0].message.content or "{}")
