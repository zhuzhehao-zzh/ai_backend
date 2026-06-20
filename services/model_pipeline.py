"""Feed consolidated student data to the LLM and parse the structured report."""

import json
import logging
import os
import re
from pathlib import Path

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1"),
    api_key=os.getenv("MOONSHOT_API_KEY"),
)


def _extract_json(raw: str) -> dict:
    """Try to parse JSON; fallback: extract from markdown code block."""
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

    raise ValueError(
        f"Could not extract valid JSON from model response.\n"
        f"Response preview (first 500 chars):\n{raw[:500]}"
    )


async def generate_report(data_path: Path, prompt_template_path: Path) -> dict:
    """Load data + prompt, call the model, return parsed JSON report."""
    data = json.loads(data_path.read_text(encoding="utf-8"))
    template = prompt_template_path.read_text(encoding="utf-8")

    # Embed the entire student data as a JSON string in the prompt.
    # This makes the template field-agnostic — any fields the frontend
    # sends are visible to the model.
    prompt = template.replace(
        "{student_data}",
        json.dumps(data, indent=2, ensure_ascii=False),
    )

    logger.info("Calling model with data from %s", data_path.name)

    response = await client.chat.completions.create(
        model=os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k"),
        messages=[
            {
                "role": "system",
                "content": "你是一位专业的高考志愿填报顾问。请返回合法的 JSON。",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=2000,
    )

    content = response.choices[0].message.content
    logger.info("Model response received (%s chars)", len(content))

    return _extract_json(content)
