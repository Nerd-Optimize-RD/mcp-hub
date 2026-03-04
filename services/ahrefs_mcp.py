"""
Ahrefs MCP tools — NerdOptimize
Uses Ahrefs API v3 with API Key authentication.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx

from auth.credential_store import CredentialStore

_store: CredentialStore | None = None
AHREFS_API_BASE = "https://api.ahrefs.com/v3"


def init(store: CredentialStore):
    global _store
    _store = store


def _get_api_key() -> str:
    if not _store:
        raise RuntimeError("Ahrefs service not initialized")
    creds = _store.get("ahrefs")
    if not creds or not creds.get("api_key"):
        raise ValueError("Ahrefs not connected")
    return creds["api_key"]


def _headers() -> dict:
    return {"Authorization": f"Bearer {_get_api_key()}", "Accept": "application/json"}


def _today_yyyymmdd() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


async def get_domain_rating(target: str) -> str:
    """Get Domain Rating (DR) and Ahrefs rank for a domain."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{AHREFS_API_BASE}/site-explorer/domain-rating",
                headers=_headers(),
                params={"target": target, "mode": "domain", "date": _today_yyyymmdd()},
            )
            resp.raise_for_status()
            data = resp.json()
            return json.dumps({"target": target, "data": data}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Ahrefs API error {e.response.status_code}: {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_backlinks(target: str, limit: int = 100) -> str:
    """Get backlink list with anchor text and referring domain's DR."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{AHREFS_API_BASE}/site-explorer/backlinks",
                headers=_headers(),
                params={"target": target, "limit": limit, "mode": "domain", "order_by": "domain_rating_source:desc"},
            )
            resp.raise_for_status()
            data = resp.json()
            return json.dumps({"target": target, "data": data}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Ahrefs API error {e.response.status_code}: {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_referring_domains(target: str, limit: int = 100) -> str:
    """Get referring domains summary for a target."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{AHREFS_API_BASE}/site-explorer/referring-domains",
                headers=_headers(),
                params={"target": target, "limit": limit, "mode": "domain", "order_by": "domain_rating:desc"},
            )
            resp.raise_for_status()
            data = resp.json()
            return json.dumps({"target": target, "data": data}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Ahrefs API error {e.response.status_code}: {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_organic_keywords(target: str, country: str = "us", limit: int = 100) -> str:
    """Get organic keywords that the target is currently ranking for."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{AHREFS_API_BASE}/site-explorer/organic-keywords",
                headers=_headers(),
                params={"target": target, "country": country, "limit": limit, "mode": "domain", "order_by": "traffic:desc"},
            )
            resp.raise_for_status()
            data = resp.json()
            return json.dumps({"target": target, "country": country, "data": data}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Ahrefs API error {e.response.status_code}: {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_top_pages(target: str, country: str = "us", limit: int = 50) -> str:
    """Get top pages by organic traffic."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{AHREFS_API_BASE}/site-explorer/top-pages",
                headers=_headers(),
                params={
                    "target": target,
                    "country": country,
                    "limit": limit,
                    "mode": "domain",
                    "order_by": "traffic:desc",
                    "select": "url,traffic,keywords",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return json.dumps({"target": target, "country": country, "data": data}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Ahrefs API error {e.response.status_code}: {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_competitors(target: str, country: str = "us", limit: int = 20) -> str:
    """Get competing domains in organic search."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{AHREFS_API_BASE}/site-explorer/competing-domains",
                headers=_headers(),
                params={"target": target, "country": country, "limit": limit, "mode": "domain"},
            )
            resp.raise_for_status()
            data = resp.json()
            return json.dumps({"target": target, "country": country, "data": data}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Ahrefs API error {e.response.status_code}: {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_keyword_difficulty(keyword: str, country: str = "us") -> str:
    """Get keyword difficulty score and search volume."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{AHREFS_API_BASE}/keywords-explorer/overview",
                headers=_headers(),
                params={"keywords": keyword, "country": country, "select": "keyword,difficulty,volume,clicks,cpc"},
            )
            resp.raise_for_status()
            data = resp.json()
            return json.dumps({"keyword": keyword, "country": country, "data": data}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Ahrefs API error {e.response.status_code}: {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def list_ahrefs_projects() -> str:
    """List all domains/projects in your Ahrefs account."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{AHREFS_API_BASE}/management/projects",
                headers=_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return json.dumps(data, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Ahrefs API error {e.response.status_code}: {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def list_site_audit_projects() -> str:
    """List all Site Audit projects in your Ahrefs account."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{AHREFS_API_BASE}/site-audit/projects",
                headers=_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return json.dumps(data, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Ahrefs API error {e.response.status_code}: {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def list_site_audit_issues(project_id: str, limit: int = 100) -> str:
    """List SEO issues for a Site Audit project."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{AHREFS_API_BASE}/site-audit/issues",
                headers=_headers(),
                params={"project_id": project_id, "limit": limit},
            )
            resp.raise_for_status()
            data = resp.json()
            return json.dumps(data, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Ahrefs API error {e.response.status_code}: {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def list_anchors(target: str, limit: int = 100) -> str:
    """Get anchor text distribution for backlinks to a domain."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{AHREFS_API_BASE}/site-explorer/anchors",
                headers=_headers(),
                params={"target": target, "limit": limit, "mode": "domain"},
            )
            resp.raise_for_status()
            data = resp.json()
            return json.dumps({"target": target, "data": data}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Ahrefs API error {e.response.status_code}: {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_pages_by_traffic(target: str, country: str = "us", limit: int = 50) -> str:
    """Get pages ranked by organic traffic (alternative to top-pages)."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{AHREFS_API_BASE}/site-explorer/pages-by-traffic",
                headers=_headers(),
                params={
                    "target": target,
                    "country": country,
                    "limit": limit,
                    "mode": "domain",
                    "select": "url,traffic,keywords",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return json.dumps({"target": target, "country": country, "data": data}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Ahrefs API error {e.response.status_code}: {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_subscription_limits() -> str:
    """Get Ahrefs API subscription limits and usage."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{AHREFS_API_BASE}/subscription-info/limits-and-usage",
                headers=_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return json.dumps(data, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Ahrefs API error {e.response.status_code}: {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def test_connection() -> dict:
    """Test Ahrefs API key with a lightweight call."""
    try:
        key = _get_api_key()
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{AHREFS_API_BASE}/subscription-info/limits-and-usage",
                headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
            )
            if resp.status_code == 200:
                return {"ok": True}
            elif resp.status_code == 401:
                return {"ok": False, "error": "Invalid API key"}
            else:
                return {"ok": False, "error": f"HTTP {resp.status_code}"}
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
