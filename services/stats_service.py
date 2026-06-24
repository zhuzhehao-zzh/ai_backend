"""Simple in-memory request counters."""

import threading

_total = 0
_ips = {}
_lock = threading.Lock()


def record_request(ip: str):
    """Call once per incoming request to increment counters."""
    global _total
    with _lock:
        _total += 1
        _ips[ip] = _ips.get(ip, 0) + 1


def get_stats(ip: str = None) -> dict:
    """Return current counters, optionally with per-IP breakdown."""
    with _lock:
        result = {
            "total_requests": _total,
            "unique_ips": len(_ips),
        }
        if ip:
            result["your_ip"] = ip
            result["your_requests"] = _ips.get(ip, 0)
        return result
