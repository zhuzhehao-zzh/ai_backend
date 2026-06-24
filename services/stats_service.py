"""Stats — queries the database for request counters."""

from services.database import get_request_stats


async def get_stats(ip: str = None) -> dict:
    """Return stats from DB, optionally with per-IP count."""
    stats = await get_request_stats()

    if ip:
        stats["your_ip"] = ip
        stats["your_requests"] = stats.get("per_ip", {}).get(ip, 0)

    return stats
