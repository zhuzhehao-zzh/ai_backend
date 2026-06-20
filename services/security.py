"""Security utilities: rate limiting, input sanitization, prompt boundaries."""

import time
import re
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── Rate limiter ───────────────────────────────────────────────────
# Simple in-memory sliding window per IP

RATE_LIMIT_WINDOW = 60       # seconds
RATE_LIMIT_MAX = 20          # max requests per window per IP

_rate_store = defaultdict(list)  # ip -> [timestamp, ...]


def check_rate_limit(ip: str) -> bool:
    """Return True if request is allowed, False if rate limited."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW

    # Clean old entries
    _rate_store[ip] = [t for t in _rate_store[ip] if t > window_start]

    if len(_rate_store[ip]) >= RATE_LIMIT_MAX:
        logger.warning("Rate limit hit for %s (%d in %ds)", ip, RATE_LIMIT_MAX, RATE_LIMIT_WINDOW)
        return False

    _rate_store[ip].append(now)
    return True


# ── JSON field size limits ─────────────────────────────────────────

MAX_JSON_DEPTH = 6
MAX_STRING_LENGTH = 5000
MAX_ARRAY_LENGTH = 100
MAX_OBJECT_KEYS = 50


def validate_json_depth(obj, depth=0):
    """Reject deeply nested JSON (prevent stack exhaustion attacks)."""
    if depth > MAX_JSON_DEPTH:
        raise ValueError(f"JSON nesting too deep (max {MAX_JSON_DEPTH})")
    if isinstance(obj, dict):
        if len(obj) > MAX_OBJECT_KEYS:
            raise ValueError(f"Too many keys (max {MAX_OBJECT_KEYS})")
        for v in obj.values():
            validate_json_depth(v, depth + 1)
    elif isinstance(obj, list):
        if len(obj) > MAX_ARRAY_LENGTH:
            raise ValueError(f"Array too long (max {MAX_ARRAY_LENGTH})")
        for item in obj:
            validate_json_depth(item, depth + 1)


# ── Input sanitization ─────────────────────────────────────────────

_PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|directions)",
    r"(?i)forget\s+(all\s+)?(previous|above|prior)",
    r"(?i)you\s+are\s+(now|free|a\s+different)",
    r"(?i)new\s+(instructions|prompt|rule)",
    r"(?i)system\s+prompt",
    r"(?i)override\s+(your|the)\s+(instructions|rules)",
    r"(?i)act\s+as\s+if",
    r"(?i)do\s+not\s+follow",
]


def contains_injection(text: str) -> bool:
    """Check if a text string contains prompt injection attempts."""
    if not isinstance(text, str):
        return False
    for pattern in _PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text):
            logger.warning("Prompt injection detected: %s", pattern)
            return True
    return False


def scan_data_for_injection(data: dict) -> list:
    """Walk all string values in data and return list of flagged fields."""
    flagged = []
    if not isinstance(data, dict):
        return flagged

    def _walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _walk(v, f"{path}[{i}]")
        elif isinstance(obj, str):
            if contains_injection(obj):
                flagged.append(path)

    _walk(data)
    return flagged


# ── Prompt boundary enforcement ────────────────────────────────────

PROMPT_SEPARATOR = "\n\n---\n\n[学生数据开始]\n"


def build_secure_prompt(template: str, student_data_json: str, patterns: str = "") -> str:
    """Insert hard boundaries around untrusted student data to resist injection."""
    # The key idea: wrap user data in clear delimiters so the LLM
    # treats it as DATA, not INSTRUCTIONS.
    secure_data = PROMPT_SEPARATOR + student_data_json + "\n\n[学生数据结束]"

    prompt = template.replace("{student_data}", secure_data)

    if patterns:
        prompt = prompt.replace("{historical_patterns}", patterns)
    else:
        prompt = prompt.replace("{historical_patterns}\n", "")

    return prompt
