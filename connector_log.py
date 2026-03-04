"""
Connector connection logger — tracks unique client sessions.
One entry per unique connection (by client type).
"""
from __future__ import annotations

import time
import uuid
from collections import OrderedDict

# Unique sessions: key -> entry
_machines: OrderedDict[tuple[str, str], dict] = OrderedDict()
# conn_id -> key for cleanup
_conn_to_machine: dict[str, tuple[str, str]] = {}
# Active connection count per session
_machine_active: dict[tuple[str, str], int] = {}
MAX_MACHINES = 100


def _guess_client_type(user_agent: str) -> str:
    ua = (user_agent or "").lower()
    if "claude" in ua or "anthropic" in ua:
        return "Claude"
    if "chatgpt" in ua or "openai" in ua:
        return "ChatGPT"
    if "cursor" in ua:
        return "Cursor"
    if "mcp" in ua:
        return "MCP Client"
    if user_agent:
        return "อื่นๆ"
    return "Unknown"


def _format_ts(ts: float) -> str:
    from datetime import datetime, timedelta, timezone
    tz_th = timezone(timedelta(hours=7))
    return datetime.fromtimestamp(ts, tz=tz_th).strftime("%Y-%m-%d %H:%M:%S UTC+7")


def log_connection_start(request) -> str:
    conn_id = str(uuid.uuid4())[:8]
    ua = request.headers.get("user-agent", "")
    client_ip = request.client.host if request.client else "?"
    client_type = _guess_client_type(ua)
    now = time.time()
    key = (client_ip, client_type)

    if key in _machines:
        m = _machines[key]
        m["last_activity"] = now
        m["last_activity_iso"] = _format_ts(now)
        m["connected"] = True
    else:
        # Trim if over limit
        while len(_machines) >= MAX_MACHINES:
            _machines.popitem(last=False)
        _machines[key] = {
            "connected_at": now,
            "connected_at_iso": _format_ts(now),
            "client_type": client_type,
            "client_ip": client_ip,
            "connected": True,
            "last_activity": now,
            "last_activity_iso": _format_ts(now),
        }
    _machine_active[key] = _machine_active.get(key, 0) + 1
    _conn_to_machine[conn_id] = key
    return conn_id


def log_connection_end(conn_id: str):
    key = _conn_to_machine.pop(conn_id, None)
    if key is None:
        return
    cnt = _machine_active.get(key, 1) - 1
    _machine_active[key] = max(0, cnt)
    if cnt <= 0:
        _machine_active.pop(key, None)
        if key in _machines:
            now = time.time()
            _machines[key]["connected"] = False
            _machines[key]["last_activity"] = now
            _machines[key]["last_activity_iso"] = _format_ts(now)


def get_log() -> dict:
    """Returns connector log for API."""
    entries = [
        {
            "connected_at_iso": v.get("connected_at_iso"),
            "last_activity_iso": v.get("last_activity_iso"),
            "client_type": v.get("client_type"),
            "connected": v.get("connected"),
        }
        for v in _machines.values()
    ]
    entries = sorted(entries, key=lambda x: x.get("last_activity", 0), reverse=True)[:50]
    total = len(_machines)
    active_count = sum(1 for v in _machines.values() if v.get("connected"))
    return {
        "total_connections": total,
        "active_count": active_count,
        "entries": entries,
    }
