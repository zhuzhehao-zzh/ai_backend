"""Feed consolidated student data to the LLM and parse the structured report."""

import json
import logging
from pathlib import Path

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

client = AsyncOpenAI()  # reads OPENAI_API_KEY from .env


async def generate_report(data_path: Path, prompt_template_path: Path) -> dict:
    """Load data + prompt, call the model, return parsed JSON report."""
    # 1. Load consolidated student data
    raw = data_path.read_text(encoding="utf-8")
    data = json.loads(raw)

    # 2. Load and render prompt template
    template = prompt_template_path.read_text(encoding="utf-8")
    prompt = template.format(**data)

    logger.info(
        "Calling model with data from %s and template %s",
        data_path.name,
        prompt_template_path.name,
    )

    # 3. Call OpenAI
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a college admissions consultant. "
                    "Analyze the student's profile and return a JSON report "
                    "with recommendations and action items."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=2000,
    )

    # 4. Parse response
    content = response.choices[0].message.content
    report = json.loads(content)

    logger.info("Model response received (tokens: %s)", response.usage)
    return report
