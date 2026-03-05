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


def _get_google_creds():
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
        scopes=["https://www.googleapis.com/auth/webmasters"],
    )
    google_creds.refresh(Request())
    return google_creds


def _get_service():
    return build("webmasters", "v3", credentials=_get_google_creds())


def _get_searchconsole_service():
    """URL Inspection uses searchconsole v1 (different from webmasters v3)."""
    return build("searchconsole", "v1", credentials=_get_google_creds())


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
    aggregationType: str | None = None,
    dataState: str | None = None,
    rowLimit: int = 1000,
    startRow: int = 0,
) -> str:
    """
    Get search analytics data from Google Search Console.
    Returns clicks, impressions, CTR, and average position.
    type: web, image, video, news, googleNews, discover
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
        if aggregationType:
            body["aggregationType"] = aggregationType
        if dataState:
            body["dataState"] = dataState

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


async def inspect_url(inspectionUrl: str, siteUrl: str, languageCode: str = "en-US") -> str:
    """
    Inspect a URL's index status in Google. Check if the page is indexed, indexable, and any issues.
    """
    try:
        service = _get_searchconsole_service()
        body = {
            "inspectionUrl": inspectionUrl,
            "siteUrl": siteUrl,
            "languageCode": languageCode,
        }
        result = service.urlInspection().index().inspect(body=body).execute()
        return json.dumps(result, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except HttpError as e:
        return json.dumps({"error": f"GSC API error: {e.reason}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_site(siteUrl: str) -> str:
    """Get detailed information about a specific Search Console property."""
    try:
        service = _get_service()
        result = service.sites().get(siteUrl=siteUrl).execute()
        return json.dumps(result, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except HttpError as e:
        return json.dumps({"error": f"GSC API error: {e.reason}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def list_sitemaps(siteUrl: str, sitemapIndex: str | None = None) -> str:
    """List all sitemaps submitted for a site."""
    try:
        service = _get_service()
        params: dict[str, str] = {}
        if sitemapIndex:
            params["sitemapIndex"] = sitemapIndex
        result = service.sitemaps().list(siteUrl=siteUrl, **params).execute()
        sitemaps = result.get("sitemap", [])
        return json.dumps({"siteUrl": siteUrl, "sitemaps": sitemaps, "count": len(sitemaps)}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except HttpError as e:
        return json.dumps({"error": f"GSC API error: {e.reason}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_sitemap(siteUrl: str, feedpath: str) -> str:
    """Get information about a specific sitemap."""
    try:
        service = _get_service()
        result = service.sitemaps().get(siteUrl=siteUrl, feedpath=feedpath).execute()
        return json.dumps(result, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except HttpError as e:
        return json.dumps({"error": f"GSC API error: {e.reason}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def submit_sitemap(siteUrl: str, feedpath: str) -> str:
    """Submit a sitemap to Google Search Console. Requires webmasters (write) scope."""
    try:
        service = _get_service()
        service.sitemaps().submit(siteUrl=siteUrl, feedpath=feedpath).execute()
        return json.dumps({"ok": True, "message": f"Sitemap {feedpath} submitted successfully"})
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except HttpError as e:
        return json.dumps({"error": f"GSC API error: {e.reason}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def delete_sitemap(siteUrl: str, feedpath: str) -> str:
    """Delete a sitemap from Search Console. Requires webmasters (write) scope."""
    try:
        service = _get_service()
        service.sitemaps().delete(siteUrl=siteUrl, feedpath=feedpath).execute()
        return json.dumps({"ok": True, "message": f"Sitemap {feedpath} deleted"})
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
