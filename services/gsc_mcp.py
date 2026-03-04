"""
Google Search Console MCP tools — NerdOptimize
"""
from __future__ import annotations

import json
from typing import Any

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from auth.credential_store import CredentialStore

_store: CredentialStore | None = None


def init(store: CredentialStore):
    global _store
    _store = store


def _get_service():
    if not _store:
        raise RuntimeError("GSC service not initialized")
    creds = _store.get("gsc")
    if not creds:
        raise ValueError("GSC not connected")

    from google.oauth2.credentials import Credentials

    google_creds = Credentials(
        token=None,
        refresh_token=creds.get("refresh_token"),
        client_id=creds.get("client_id"),
        client_secret=creds.get("client_secret"),
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
    )
    google_creds.refresh(Request())
    return build("webmasters", "v3", credentials=google_creds)


async def list_sites() -> str:
    """List all Google Search Console properties accessible to this account."""
    try:
        service = _get_service()
        result = service.sites().list().execute()
        sites = result.get("siteEntry", [])
        if not sites:
            return json.dumps({"sites": [], "message": "No GSC properties found"})
        return json.dumps({"sites": [{"siteUrl": s["siteUrl"], "permissionLevel": s.get("permissionLevel")} for s in sites]}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except HttpError as e:
        return json.dumps({"error": f"GSC API error: {e.reason}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_search_analytics(
    siteUrl: str,
    startDate: str,
    endDate: str,
    dimensions: list[str] | None = None,
    type: str = "web",
    dimensionFilterGroups: list[dict] | None = None,
    rowLimit: int = 1000,
    startRow: int = 0,
) -> str:
    """
    Get search analytics data from Google Search Console.
    Returns clicks, impressions, CTR, and average position.
    """
    try:
        service = _get_service()

        body: dict[str, Any] = {
            "startDate": startDate,
            "endDate": endDate,
            "type": type,
            "rowLimit": min(rowLimit, 25000),
            "startRow": startRow,
        }
        if dimensions:
            body["dimensions"] = dimensions
        if dimensionFilterGroups:
            body["dimensionFilterGroups"] = dimensionFilterGroups

        result = service.searchanalytics().query(siteUrl=siteUrl, body=body).execute()
        rows = result.get("rows", [])

        formatted_rows = []
        for row in rows:
            item = {
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": round(row.get("ctr", 0), 4),
                "position": round(row.get("position", 0), 1),
            }
            if dimensions and "keys" in row:
                for i, dim in enumerate(dimensions):
                    item[dim] = row["keys"][i] if i < len(row["keys"]) else None
            formatted_rows.append(item)

        return json.dumps({
            "siteUrl": siteUrl,
            "dateRange": {"startDate": startDate, "endDate": endDate},
            "dimensions": dimensions or [],
            "rowCount": len(formatted_rows),
            "rows": formatted_rows,
        }, indent=2)

    except ValueError as e:
        return json.dumps({"error": str(e)})
    except HttpError as e:
        return json.dumps({"error": f"GSC API error: {e.reason}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def test_connection() -> dict:
    """Test GSC connection and return status."""
    try:
        service = _get_service()
        result = service.sites().list().execute()
        sites = result.get("siteEntry", [])
        return {"ok": True, "sites_count": len(sites)}
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
