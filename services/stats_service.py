"""Simple in-memory request counters."""

import threading

_total = 0
_ips = set()
_lock = threading.Lock()


def record_request(ip: str):
    """Call once per incoming request to increment counters."""
    global _total
    with _lock:
        _total += 1
        _ips.add(ip)


def get_stats() -> dict:
    """Return current counters."""
    with _lock:
        return {
            "total_requests": _total,
            "unique_ips": len(_ips),
        }
