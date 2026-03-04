"""
Google Analytics 4 MCP tools — NerdOptimize
"""
from __future__ import annotations

import json
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from auth.credential_store import CredentialStore

_store: CredentialStore | None = None


def init(store: CredentialStore):
    global _store
    _store = store


def _get_credentials() -> Credentials:
    if not _store:
        raise RuntimeError("GA4 service not initialized")
    creds_data = _store.get("ga4")
    if not creds_data:
        raise ValueError("GA4 not connected")

    creds = Credentials(
        token=None,
        refresh_token=creds_data.get("refresh_token"),
        client_id=creds_data.get("client_id"),
        client_secret=creds_data.get("client_secret"),
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/analytics.readonly"],
    )
    creds.refresh(Request())
    return creds


def _run_report(property_id: str, body: dict) -> dict:
    from googleapiclient.discovery import build
    creds = _get_credentials()
    service = build("analyticsdata", "v1beta", credentials=creds)
    return service.properties().runReport(property=f"properties/{property_id}", body=body).execute()


def _format_report(response: dict) -> list[dict]:
    dim_headers = [h["name"] for h in response.get("dimensionHeaders", [])]
    met_headers = [h["name"] for h in response.get("metricHeaders", [])]
    rows = []
    for row in response.get("rows", []):
        item = {}
        for i, val in enumerate(row.get("dimensionValues", [])):
            if i < len(dim_headers):
                item[dim_headers[i]] = val.get("value")
        for i, val in enumerate(row.get("metricValues", [])):
            if i < len(met_headers):
                v = val.get("value", "0")
                try:
                    item[met_headers[i]] = float(v) if "." in v else int(v)
                except (ValueError, TypeError):
                    item[met_headers[i]] = v
        rows.append(item)
    return rows


async def list_ga4_properties() -> str:
    """List all GA4 properties accessible to this account. Always start here to get property_id."""
    try:
        from googleapiclient.discovery import build
        creds = _get_credentials()
        admin = build("analyticsadmin", "v1beta", credentials=creds)
        # Use accountSummaries.list - no filter needed, works across all accounts
        output = []
        page_token = None
        while True:
            result = admin.accountSummaries().list(
                pageSize=200,
                pageToken=page_token,
            ).execute()
            for acc in result.get("accountSummaries", []):
                account_id = acc.get("account", "").replace("accounts/", "")
                account_name = acc.get("displayName", "")
                for ps in acc.get("propertySummaries", []):
                    prop_id = ps.get("property", "").replace("properties/", "")
                    if prop_id:
                        output.append({
                            "property_id": prop_id,
                            "display_name": ps.get("displayName"),
                            "account_id": account_id,
                            "account_name": account_name,
                        })
            page_token = result.get("nextPageToken")
            if not page_token:
                break
        return json.dumps({"properties": output, "count": len(output)}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_recommended_analytics(property_id: str, date_range_start: str = "30daysAgo", date_range_end: str = "today") -> str:
    """Get comprehensive analytics overview with all recommended dimensions and metrics."""
    try:
        body = {
            "dateRanges": [{"startDate": date_range_start, "endDate": date_range_end}],
            "dimensions": [{"name": "sessionSourceMedium"}, {"name": "deviceCategory"}],
            "metrics": [
                {"name": "sessions"},
                {"name": "totalUsers"},
                {"name": "keyEvents"},
                {"name": "engagementRate"},
                {"name": "bounceRate"},
                {"name": "averageSessionDuration"},
            ],
            "limit": 50,
        }
        response = _run_report(property_id, body)
        rows = _format_report(response)
        return json.dumps({"property_id": property_id, "dateRange": {"start": date_range_start, "end": date_range_end}, "rows": rows, "rowCount": len(rows)}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_ga4_data(
    property_id: str,
    dimensions: list[str],
    metrics: list[str],
    date_range_start: str = "30daysAgo",
    date_range_end: str = "today",
    limit: int = 100,
) -> str:
    """Get custom GA4 data with user-specified dimensions and metrics."""
    try:
        body = {
            "dateRanges": [{"startDate": date_range_start, "endDate": date_range_end}],
            "dimensions": [{"name": d} for d in dimensions],
            "metrics": [{"name": m} for m in metrics],
            "limit": limit,
        }
        response = _run_report(property_id, body)
        rows = _format_report(response)
        return json.dumps({"property_id": property_id, "dimensions": dimensions, "metrics": metrics, "rows": rows, "rowCount": len(rows)}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_top_pages(property_id: str, date_range_start: str = "30daysAgo", date_range_end: str = "today", limit: int = 25) -> str:
    """Get top pages ranked by sessions with engagement metrics."""
    try:
        body = {
            "dateRanges": [{"startDate": date_range_start, "endDate": date_range_end}],
            "dimensions": [{"name": "pagePath"}, {"name": "pageTitle"}],
            "metrics": [{"name": "sessions"}, {"name": "totalUsers"}, {"name": "engagementRate"}, {"name": "averageSessionDuration"}, {"name": "keyEvents"}],
            "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
            "limit": limit,
        }
        response = _run_report(property_id, body)
        rows = _format_report(response)
        return json.dumps({"property_id": property_id, "rows": rows, "rowCount": len(rows)}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_traffic_sources(property_id: str, date_range_start: str = "30daysAgo", date_range_end: str = "today", limit: int = 25) -> str:
    """Get traffic sources breakdown — where visitors come from."""
    try:
        body = {
            "dateRanges": [{"startDate": date_range_start, "endDate": date_range_end}],
            "dimensions": [{"name": "sessionSourceMedium"}],
            "metrics": [{"name": "sessions"}, {"name": "totalUsers"}, {"name": "keyEvents"}, {"name": "engagementRate"}, {"name": "bounceRate"}],
            "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
            "limit": limit,
        }
        response = _run_report(property_id, body)
        rows = _format_report(response)
        return json.dumps({"property_id": property_id, "rows": rows, "rowCount": len(rows)}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_device_breakdown(property_id: str, date_range_start: str = "30daysAgo", date_range_end: str = "today") -> str:
    """Get visitor breakdown by device (desktop / mobile / tablet)."""
    try:
        body = {
            "dateRanges": [{"startDate": date_range_start, "endDate": date_range_end}],
            "dimensions": [{"name": "deviceCategory"}],
            "metrics": [{"name": "sessions"}, {"name": "totalUsers"}, {"name": "engagementRate"}, {"name": "bounceRate"}],
            "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
        }
        response = _run_report(property_id, body)
        rows = _format_report(response)
        return json.dumps({"property_id": property_id, "rows": rows}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_conversion_report(property_id: str, date_range_start: str = "30daysAgo", date_range_end: str = "today", limit: int = 25) -> str:
    """Get key events/conversion report by source, page, and event name."""
    try:
        body = {
            "dateRanges": [{"startDate": date_range_start, "endDate": date_range_end}],
            "dimensions": [{"name": "eventName"}, {"name": "sessionSourceMedium"}],
            "metrics": [{"name": "keyEvents"}, {"name": "totalUsers"}, {"name": "sessionKeyEventRate"}],
            "orderBys": [{"metric": {"metricName": "keyEvents"}, "desc": True}],
            "limit": limit,
        }
        response = _run_report(property_id, body)
        rows = _format_report(response)
        return json.dumps({"property_id": property_id, "rows": rows, "rowCount": len(rows)}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_audience_report(property_id: str, date_range_start: str = "30daysAgo", date_range_end: str = "today") -> str:
    """Get audience demographics (age, gender, geo). Must be enabled in GA4 settings first."""
    try:
        body = {
            "dateRanges": [{"startDate": date_range_start, "endDate": date_range_end}],
            "dimensions": [{"name": "country"}, {"name": "city"}],
            "metrics": [{"name": "totalUsers"}, {"name": "sessions"}, {"name": "engagementRate"}],
            "orderBys": [{"metric": {"metricName": "totalUsers"}, "desc": True}],
            "limit": 50,
        }
        response = _run_report(property_id, body)
        rows = _format_report(response)
        return json.dumps({"property_id": property_id, "rows": rows, "rowCount": len(rows)}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_realtime_data(property_id: str) -> str:
    """Get realtime data — who is on the site right now."""
    try:
        from googleapiclient.discovery import build
        creds = _get_credentials()
        service = build("analyticsdata", "v1beta", credentials=creds)
        response = service.properties().runRealtimeReport(
            property=f"properties/{property_id}",
            body={
                "dimensions": [{"name": "country"}, {"name": "pagePath"}],
                "metrics": [{"name": "activeUsers"}],
            }
        ).execute()
        rows = _format_report(response)
        return json.dumps({"property_id": property_id, "realtime": True, "rows": rows}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_realtime_active_users(property_id: str) -> str:
    """Get count of active users right now (lightweight call)."""
    try:
        from googleapiclient.discovery import build
        creds = _get_credentials()
        service = build("analyticsdata", "v1beta", credentials=creds)
        response = service.properties().runRealtimeReport(
            property=f"properties/{property_id}",
            body={"metrics": [{"name": "activeUsers"}]},
        ).execute()
        rows = response.get("rows", [])
        count = int(rows[0]["metricValues"][0]["value"]) if rows else 0
        return json.dumps({"property_id": property_id, "activeUsers": count})
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def compare_date_ranges(
    property_id: str,
    current_start: str,
    current_end: str,
    previous_start: str,
    previous_end: str,
    metrics: list[str] | None = None,
) -> str:
    """Compare metrics between two date ranges."""
    try:
        if not metrics:
            metrics = ["sessions", "totalUsers", "keyEvents", "engagementRate"]
        body = {
            "dateRanges": [
                {"startDate": current_start, "endDate": current_end, "name": "current"},
                {"startDate": previous_start, "endDate": previous_end, "name": "previous"},
            ],
            "metrics": [{"name": m} for m in metrics],
        }
        from googleapiclient.discovery import build
        creds = _get_credentials()
        service = build("analyticsdata", "v1beta", credentials=creds)
        response = service.properties().runReport(property=f"properties/{property_id}", body=body).execute()
        return json.dumps({"property_id": property_id, "comparison": response.get("rows", [])}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def run_funnel_report(property_id: str, steps: list[str], date_range_start: str = "30daysAgo", date_range_end: str = "today") -> str:
    """Run funnel report tracking user journey through events."""
    try:
        from googleapiclient.discovery import build
        creds = _get_credentials()
        service = build("analyticsdata", "v1beta", credentials=creds)

        funnel_steps = [
            {"name": step, "filterExpression": {"funnelFieldFilter": {"fieldName": "eventName", "stringFilter": {"matchType": "EXACT", "value": step}}}}
            for step in steps
        ]

        body = {
            "dateRange": {"startDate": date_range_start, "endDate": date_range_end},
            "funnel": {"steps": funnel_steps},
        }
        response = service.properties().runFunnelReport(property=f"properties/{property_id}", body=body).execute()
        return json.dumps({"property_id": property_id, "funnel_steps": steps, "result": response}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def search_schema(property_id: str, keyword: str) -> str:
    """Search for dimensions/metrics by keyword."""
    try:
        from googleapiclient.discovery import build
        creds = _get_credentials()
        service = build("analyticsdata", "v1beta", credentials=creds)
        response = service.properties().getMetadata(name=f"properties/{property_id}/metadata").execute()
        kw = keyword.lower()
        dims = [d for d in response.get("dimensions", []) if kw in d.get("apiName", "").lower() or kw in d.get("uiName", "").lower()]
        mets = [m for m in response.get("metrics", []) if kw in m.get("apiName", "").lower() or kw in m.get("uiName", "").lower()]
        return json.dumps({"keyword": keyword, "dimensions": dims[:20], "metrics": mets[:20]}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def list_dimension_categories(property_id: str) -> str:
    """List all dimension categories available for this property."""
    try:
        from googleapiclient.discovery import build
        creds = _get_credentials()
        service = build("analyticsdata", "v1beta", credentials=creds)
        response = service.properties().getMetadata(name=f"properties/{property_id}/metadata").execute()
        categories = list({d.get("category", "Other") for d in response.get("dimensions", [])})
        return json.dumps({"property_id": property_id, "dimension_categories": sorted(categories)}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def list_metric_categories(property_id: str) -> str:
    """List all metric categories available for this property."""
    try:
        from googleapiclient.discovery import build
        creds = _get_credentials()
        service = build("analyticsdata", "v1beta", credentials=creds)
        response = service.properties().getMetadata(name=f"properties/{property_id}/metadata").execute()
        categories = list({m.get("category", "Other") for m in response.get("metrics", [])})
        return json.dumps({"property_id": property_id, "metric_categories": sorted(categories)}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_dimensions_by_category(property_id: str, category: str) -> str:
    """Get all dimensions in a specific category."""
    try:
        from googleapiclient.discovery import build
        creds = _get_credentials()
        service = build("analyticsdata", "v1beta", credentials=creds)
        response = service.properties().getMetadata(name=f"properties/{property_id}/metadata").execute()
        dims = [d for d in response.get("dimensions", []) if d.get("category", "").lower() == category.lower()]
        return json.dumps({"property_id": property_id, "category": category, "dimensions": dims}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def get_metrics_by_category(property_id: str, category: str) -> str:
    """Get all metrics in a specific category."""
    try:
        from googleapiclient.discovery import build
        creds = _get_credentials()
        service = build("analyticsdata", "v1beta", credentials=creds)
        response = service.properties().getMetadata(name=f"properties/{property_id}/metadata").execute()
        mets = [m for m in response.get("metrics", []) if m.get("category", "").lower() == category.lower()]
        return json.dumps({"property_id": property_id, "category": category, "metrics": mets}, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def test_connection() -> dict:
    """Test GA4 connection."""
    try:
        _get_credentials()
        return {"ok": True}
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
