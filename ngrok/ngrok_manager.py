"""
ngrok tunnel manager — NerdOptimize
Uses pyngrok to manage the ngrok tunnel.
"""
from __future__ import annotations

from auth.credential_store import CredentialStore

_store: CredentialStore | None = None
_tunnel = None


def init(store: CredentialStore):
    global _store
    _store = store


def connect(authtoken: str, static_domain: str) -> dict:
    """Connect ngrok with authtoken and static domain."""
    global _tunnel

    try:
        from pyngrok import ngrok, conf

        conf.get_default().auth_token = authtoken

        if _tunnel:
            try:
                ngrok.disconnect(_tunnel.public_url)
            except Exception:
                pass
            _tunnel = None

        _tunnel = ngrok.connect(
            8000,
            "http",
            domain=static_domain,
        )

        mcp_url = f"https://{static_domain}/mcp-hub/sse"

        if _store:
            _store.set("ngrok", {
                "authtoken": authtoken,
                "static_domain": static_domain,
                "mcp_url": mcp_url,
            })

        return {"ok": True, "mcp_url": mcp_url, "public_url": _tunnel.public_url}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def stop_tunnel() -> dict:
    """Stop ngrok tunnel only (keep credentials for reconnect)."""
    global _tunnel
    try:
        from pyngrok import ngrok
        if _tunnel:
            ngrok.disconnect(_tunnel.public_url)
            _tunnel = None
        ngrok.kill()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def disconnect() -> dict:
    """Disconnect ngrok tunnel and delete credentials."""
    global _tunnel
    try:
        from pyngrok import ngrok
        if _tunnel:
            ngrok.disconnect(_tunnel.public_url)
            _tunnel = None
        ngrok.kill()
        if _store:
            _store.delete("ngrok")
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_status() -> dict:
    """Get current ngrok status."""
    if _tunnel:
        return {"connected": True, "public_url": _tunnel.public_url}

    if _store:
        creds = _store.get("ngrok")
        if creds:
            domain = creds.get("static_domain", "")
            return {
                "connected": False,
                "has_credentials": True,
                "static_domain": domain,
                "mcp_url": creds.get("mcp_url", ""),
            }

    return {"connected": False, "has_credentials": False}


def is_connected() -> bool:
    return _tunnel is not None
