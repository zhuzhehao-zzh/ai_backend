"""Statistics service — reads from server logs to compute usage metrics."""

import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

LOG_DIR = "/root/Desktop/career/log"


def get_stats() -> dict:
    """Parse server logs and return usage statistics."""
    log_dir = Path(LOG_DIR)
    if not log_dir.exists():
        return {"error": "Log directory not found", "total_requests": 0, "unique_ips": 0}

    total = 0
    ips = set()
    requests_by_date = {}

    # REQUEST log format: "REQUEST  | <ip> | <uuid> | keys=..."
    pattern = re.compile(r"(\d{4}-\d{2}-\d{2}).*\[routes\.api\].*REQUEST\s+\|\s+([\d\.]+)\s+\|")

    for log_file in sorted(log_dir.glob("server-*.log")):
        try:
            for line in log_file.read_text(encoding="utf-8").splitlines():
                m = pattern.search(line)
                if m:
                    date, ip = m.group(1), m.group(2)
                    total += 1
                    ips.add(ip)
                    requests_by_date[date] = requests_by_date.get(date, 0) + 1
        except Exception as e:
            logger.warning("Failed to read %s: %s", log_file, e)

    return {
        "total_requests": total,
        "unique_ips": len(ips),
        "requests_by_date": dict(sorted(requests_by_date.items())),
    }
