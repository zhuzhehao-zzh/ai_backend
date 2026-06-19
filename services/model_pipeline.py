"""Feed consolidated student data to the LLM and parse the structured report."""

import json
import logging
import os
from pathlib import Path

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Moonshot AI (Kimi) — OpenAI-compatible, just swap base_url & model.
# Base URL can be overridden via MOONSHOT_BASE_URL env var.
client = AsyncOpenAI(
    base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1"),
    api_key=os.getenv("MOONSHOT_API_KEY"),
)


async def generate_report(data_path: Path, prompt_template_path: Path) -> dict:
    """Load data + prompt, call the model, return parsed JSON report."""
    # 1. Load consolidated student data
    raw = data_path.read_text(encoding="utf-8")
    data = json.loads(raw)

    # 2. Load and render prompt template
    template = prompt_template_path.read_text(encoding="utf-8")
    # Fill missing keys with empty strings so template.format() never KeyErrors
    defaults = {k: "" for k in ("full_name", "email", "high_school", "graduation_year",
                                 "gpa", "sat_score", "act_score", "intended_majors",
                                 "coursework", "preferred_regions", "budget_range",
                                 "extracurriculars", "awards", "personal_statement")}
    defaults.update(data)
    prompt = template.format(**defaults)

    logger.info(
        "Calling model with data from %s and template %s",
        data_path.name,
        prompt_template_path.name,
    )

    # 3. Call Moonshot AI (Kimi)
    response = await client.chat.completions.create(
        model=os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k"),
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
