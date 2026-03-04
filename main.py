"""
MCP Hub — FastAPI Entry Point
NerdOptimize
"""
from __future__ import annotations

import json
import os
import tempfile
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import (
    CallToolResult,
    TextContent,
    Tool,
)

from auth.credential_store import CredentialStore
from auth.oauth_handler import OAuthHandler, handle_callback as oauth_handle_callback
from connector_log import get_log, log_connection_end, log_connection_start
from middleware.service_dispatcher import TOOL_REGISTRY, TOOL_SERVICE_MAP, dispatch
from ngrok import ngrok_manager
from services import ahrefs_mcp, ga4_mcp, gsc_mcp

# ─── Init ─────────────────────────────────────────────────────────────────────

DATA_PATH = os.environ.get("CREDENTIALS_PATH", "/data/credentials.json")
UPLOAD_META_PATH = os.path.join(os.path.dirname(DATA_PATH), "upload_meta.json")
credential_store = CredentialStore(DATA_PATH)


def _read_upload_meta() -> dict:
    try:
        with open(UPLOAD_META_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write_upload_meta(data: dict):
    os.makedirs(os.path.dirname(UPLOAD_META_PATH), exist_ok=True)
    with open(UPLOAD_META_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _clear_upload_meta(service: str):
    meta = _read_upload_meta()
    meta.pop(service, None)
    _write_upload_meta(meta)


oauth_handler = OAuthHandler(credential_store)

gsc_mcp.init(credential_store)
ga4_mcp.init(credential_store)
ahrefs_mcp.init(credential_store)
ngrok_manager.init(credential_store)

# ─── MCP Server ───────────────────────────────────────────────────────────────

mcp_server = Server("mcp-hub")


def _is_service_connected(service: str) -> bool:
    return credential_store.has_service(service)


@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    tools = []

    if _is_service_connected("gsc"):
        tools += [
            Tool(
                name="list_sites",
                description="List all Google Search Console properties accessible to this account.",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="get_search_analytics",
                description="Get search analytics data (clicks, impressions, CTR, position) from Google Search Console.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "siteUrl": {"type": "string", "description": "Property URL e.g. https://example.com/"},
                        "startDate": {"type": "string", "description": "Start date YYYY-MM-DD"},
                        "endDate": {"type": "string", "description": "End date YYYY-MM-DD"},
                        "dimensions": {"type": "array", "items": {"type": "string"}, "description": "query, page, country, device, date"},
                        "type": {"type": "string", "description": "web, image, video, news", "default": "web"},
                        "dimensionFilterGroups": {"type": "array", "items": {"type": "object"}},
                        "rowLimit": {"type": "integer", "default": 1000, "description": "Max rows (default 1000, max 25000)"},
                        "startRow": {"type": "integer", "default": 0},
                    },
                    "required": ["siteUrl", "startDate", "endDate"],
                },
            ),
        ]

    if _is_service_connected("ga4"):
        tools += [
            Tool(name="list_ga4_properties", description="List all GA4 properties. Always start here to get property_id.", inputSchema={"type": "object", "properties": {}, "required": []}),
            Tool(name="get_recommended_analytics", description="Get comprehensive analytics overview with recommended dimensions and metrics.", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}, "date_range_start": {"type": "string", "default": "30daysAgo"}, "date_range_end": {"type": "string", "default": "today"}}, "required": ["property_id"]}),
            Tool(name="get_ga4_data", description="Get custom GA4 data with user-specified dimensions and metrics.", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}, "dimensions": {"type": "array", "items": {"type": "string"}}, "metrics": {"type": "array", "items": {"type": "string"}}, "date_range_start": {"type": "string", "default": "30daysAgo"}, "date_range_end": {"type": "string", "default": "today"}, "limit": {"type": "integer", "default": 100}}, "required": ["property_id", "dimensions", "metrics"]}),
            Tool(name="get_top_pages_ga4", description="Get top pages ranked by sessions with engagement metrics.", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}, "date_range_start": {"type": "string", "default": "30daysAgo"}, "date_range_end": {"type": "string", "default": "today"}, "limit": {"type": "integer", "default": 25}}, "required": ["property_id"]}),
            Tool(name="get_traffic_sources", description="Get traffic sources breakdown — where visitors come from.", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}, "date_range_start": {"type": "string"}, "date_range_end": {"type": "string"}, "limit": {"type": "integer", "default": 25}}, "required": ["property_id"]}),
            Tool(name="get_device_breakdown", description="Get visitor breakdown by device (desktop/mobile/tablet).", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}, "date_range_start": {"type": "string"}, "date_range_end": {"type": "string"}}, "required": ["property_id"]}),
            Tool(name="get_conversion_report", description="Get key events/conversion report by source, page, and event name.", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}, "date_range_start": {"type": "string"}, "date_range_end": {"type": "string"}, "limit": {"type": "integer", "default": 25}}, "required": ["property_id"]}),
            Tool(name="get_audience_report", description="Get audience demographics (country, city). Must be enabled in GA4 settings first.", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}, "date_range_start": {"type": "string"}, "date_range_end": {"type": "string"}}, "required": ["property_id"]}),
            Tool(name="get_realtime_data", description="Get realtime data — who is on the site right now.", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}}, "required": ["property_id"]}),
            Tool(name="get_realtime_active_users", description="Get count of active users right now (lightweight).", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}}, "required": ["property_id"]}),
            Tool(name="compare_date_ranges", description="Compare metrics between two date ranges.", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}, "current_start": {"type": "string"}, "current_end": {"type": "string"}, "previous_start": {"type": "string"}, "previous_end": {"type": "string"}, "metrics": {"type": "array", "items": {"type": "string"}}}, "required": ["property_id", "current_start", "current_end", "previous_start", "previous_end"]}),
            Tool(name="run_funnel_report", description="Run funnel report tracking user journey through events.", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}, "steps": {"type": "array", "items": {"type": "string"}}, "date_range_start": {"type": "string"}, "date_range_end": {"type": "string"}}, "required": ["property_id", "steps"]}),
            Tool(name="search_schema", description="Search for GA4 dimensions/metrics by keyword.", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}, "keyword": {"type": "string"}}, "required": ["property_id", "keyword"]}),
            Tool(name="list_dimension_categories", description="List all dimension categories for this GA4 property.", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}}, "required": ["property_id"]}),
            Tool(name="list_metric_categories", description="List all metric categories for this GA4 property.", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}}, "required": ["property_id"]}),
            Tool(name="get_dimensions_by_category", description="Get all dimensions in a specific GA4 category.", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}, "category": {"type": "string"}}, "required": ["property_id", "category"]}),
            Tool(name="get_metrics_by_category", description="Get all metrics in a specific GA4 category.", inputSchema={"type": "object", "properties": {"property_id": {"type": "string"}, "category": {"type": "string"}}, "required": ["property_id", "category"]}),
        ]

    if _is_service_connected("ahrefs"):
        tools += [
            Tool(name="list_ahrefs_projects", description="List all domains/projects in your Ahrefs account. Use this first to get domain list.", inputSchema={"type": "object", "properties": {}, "required": []}),
            Tool(name="get_domain_rating", description="Get Domain Rating (DR) and Ahrefs rank for a domain.", inputSchema={"type": "object", "properties": {"target": {"type": "string", "description": "Domain e.g. example.com"}}, "required": ["target"]}),
            Tool(name="get_backlinks", description="Get backlink list with anchor text and referring domain DR.", inputSchema={"type": "object", "properties": {"target": {"type": "string"}, "limit": {"type": "integer", "default": 100}}, "required": ["target"]}),
            Tool(name="get_referring_domains", description="Get referring domains summary.", inputSchema={"type": "object", "properties": {"target": {"type": "string"}, "limit": {"type": "integer", "default": 100}}, "required": ["target"]}),
            Tool(name="get_organic_keywords", description="Get organic keywords the target is currently ranking for.", inputSchema={"type": "object", "properties": {"target": {"type": "string"}, "country": {"type": "string", "default": "us"}, "limit": {"type": "integer", "default": 100}}, "required": ["target"]}),
            Tool(name="get_top_pages", description="Get top pages by organic traffic.", inputSchema={"type": "object", "properties": {"target": {"type": "string"}, "country": {"type": "string", "default": "us"}, "limit": {"type": "integer", "default": 50}}, "required": ["target"]}),
            Tool(name="get_competitors", description="Get competing domains in organic search.", inputSchema={"type": "object", "properties": {"target": {"type": "string"}, "country": {"type": "string", "default": "us"}, "limit": {"type": "integer", "default": 20}}, "required": ["target"]}),
            Tool(name="get_keyword_difficulty", description="Get keyword difficulty score and search volume.", inputSchema={"type": "object", "properties": {"keyword": {"type": "string"}, "country": {"type": "string", "default": "us"}}, "required": ["keyword"]}),
            Tool(name="list_site_audit_projects", description="List Site Audit projects in Ahrefs account.", inputSchema={"type": "object", "properties": {}, "required": []}),
            Tool(name="list_site_audit_issues", description="List SEO issues for a Site Audit project.", inputSchema={"type": "object", "properties": {"project_id": {"type": "string"}, "limit": {"type": "integer", "default": 100}}, "required": ["project_id"]}),
            Tool(name="list_anchors", description="Get anchor text distribution for backlinks to a domain.", inputSchema={"type": "object", "properties": {"target": {"type": "string"}, "limit": {"type": "integer", "default": 100}}, "required": ["target"]}),
            Tool(name="get_pages_by_traffic", description="Get pages ranked by organic traffic.", inputSchema={"type": "object", "properties": {"target": {"type": "string"}, "country": {"type": "string", "default": "us"}, "limit": {"type": "integer", "default": 50}}, "required": ["target"]}),
            Tool(name="get_subscription_limits", description="Get Ahrefs API subscription limits and usage.", inputSchema={"type": "object", "properties": {}, "required": []}),
        ]

    return tools


@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    service = TOOL_SERVICE_MAP.get(name)
    if service and not _is_service_connected(service):
        return [TextContent(type="text", text=json.dumps({"error": f"{service.upper()} is not connected. Please connect it in the MCP Hub Setup Panel."}))]

    result = await dispatch(name, arguments or {})
    return [TextContent(type="text", text=result)]


# ─── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(title="MCP Hub API", version="1.0.0", description="NerdOptimize MCP Hub")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SSE Transport
sse_transport = SseServerTransport("/mcp-hub/messages")


@app.get("/mcp-hub/sse")
async def mcp_sse_endpoint(request: Request):
    conn_id = log_connection_start(request)
    try:
        async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
            await mcp_server.run(streams[0], streams[1], mcp_server.create_initialization_options())
    except RuntimeError as e:
        if "after response already completed" not in str(e):
            raise
        # Expected when client disconnects; suppress noisy log
    finally:
        log_connection_end(conn_id)


@app.post("/mcp-hub/messages")
async def mcp_messages_endpoint(request: Request):
    try:
        await sse_transport.handle_post_message(request.scope, request.receive, request._send)
    except RuntimeError as e:
        if "after response already completed" not in str(e):
            raise
        # Expected when client disconnects; suppress noisy log


# ─── API: Status ──────────────────────────────────────────────────────────────

@app.get("/api/status")
async def get_status():
    gsc_creds = credential_store.get("gsc")
    ga4_creds = credential_store.get("ga4")
    ahrefs_creds = credential_store.get("ahrefs")
    ngrok_creds = credential_store.get("ngrok")
    upload_meta = _read_upload_meta()

    return {
        "gsc": {
            "has_credentials": gsc_creds is not None,
            "status": gsc_creds.get("status", "disconnected") if gsc_creds else "disconnected",
            "connected_at": gsc_creds.get("connected_at") if gsc_creds else None,
            "uploaded_filename": upload_meta.get("gsc"),
        },
        "ga4": {
            "has_credentials": ga4_creds is not None,
            "status": ga4_creds.get("status", "disconnected") if ga4_creds else "disconnected",
            "connected_at": ga4_creds.get("connected_at") if ga4_creds else None,
            "uploaded_filename": upload_meta.get("ga4"),
        },
        "ahrefs": {
            "has_credentials": ahrefs_creds is not None,
            "status": ahrefs_creds.get("status", "disconnected") if ahrefs_creds else "disconnected",
            "connected_at": ahrefs_creds.get("connected_at") if ahrefs_creds else None,
        },
        "ngrok": {
            "has_credentials": ngrok_creds is not None,
            "status": ngrok_creds.get("status", "disconnected") if ngrok_creds else "disconnected",
            "mcp_url": ngrok_creds.get("mcp_url") if ngrok_creds else None,
            "static_domain": ngrok_creds.get("static_domain") if ngrok_creds else None,
            "tunnel_active": ngrok_manager.is_connected(),
        },
        "mcp_hub": {
            "online": ngrok_manager.is_connected(),
        },
    }


# ─── API: GSC / GA4 OAuth ─────────────────────────────────────────────────────

@app.post("/api/upload-secret/{service}")
async def upload_secret(service: str, file: UploadFile = File(...)):
    if service not in ("gsc", "ga4"):
        raise HTTPException(400, f"Unknown service: {service}")
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON file")

    # Validate it's a Google client secret
    if "installed" not in data and "web" not in data:
        raise HTTPException(400, "Not a valid Google client_secret.json")

    # Store temporarily so OAuth flow can use it
    tmp_path = f"/tmp/client_secret_{service}.json"
    with open(tmp_path, "w") as f:
        json.dump(data, f)

    # Persist filename for UI display
    filename = file.filename or "client_secret.json"
    meta = _read_upload_meta()
    meta[service] = filename
    _write_upload_meta(meta)

    return {"ok": True, "message": f"client_secret.json for {service.upper()} uploaded successfully", "filename": filename}


@app.delete("/api/upload-secret/{service}")
async def clear_upload_secret(service: str):
    if service not in ("gsc", "ga4"):
        raise HTTPException(400, f"Unknown service: {service}")
    tmp_path = f"/tmp/client_secret_{service}.json"
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)
    _clear_upload_meta(service)
    return {"ok": True, "message": f"{service.upper()} upload cleared"}


@app.get("/api/oauth/start/{service}")
async def oauth_start(service: str):
    if service not in ("gsc", "ga4"):
        raise HTTPException(400, f"Unknown service: {service}")

    tmp_path = f"/tmp/client_secret_{service}.json"
    if not os.path.exists(tmp_path):
        raise HTTPException(400, f"Please upload client_secret.json for {service.upper()} first")

    with open(tmp_path, "r") as f:
        client_secret_json = f.read()

    auth_url = oauth_handler.start_oauth(service, client_secret_json)

    # Keep file until OAuth succeeds (allows retry without re-upload)
    return {"ok": True, "auth_url": auth_url}


@app.get("/api/oauth/callback", response_class=HTMLResponse)
async def oauth_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    """OAuth callback — Google redirects here. Returns HTML for popup display."""
    html, status = oauth_handle_callback(code, state, error)
    return HTMLResponse(content=html, status_code=status)


@app.get("/api/oauth/poll/{service}")
async def oauth_poll(service: str):
    """Frontend polls this to check if OAuth completed."""
    result = oauth_handler.get_oauth_result(service)
    if result is None:
        return {"status": "pending"}
    if result.get("success"):
        return {"status": "connected"}
    return {"status": "error", "error": result.get("error", "Unknown error")}


# ─── API: Ahrefs ──────────────────────────────────────────────────────────────

def _mask_value(val: str, prefix_len: int = 4, suffix_len: int = 4, mid_char: str = "x") -> str:
    if not val or len(val) <= prefix_len + suffix_len:
        return mid_char * 8
    return val[:prefix_len] + mid_char * (len(val) - prefix_len - suffix_len) + val[-suffix_len:]


def _mask_ngrok_token(val: str) -> str:
    if not val:
        return ""
    return _mask_value(val, 4, 4)


@app.get("/api/credentials/ahrefs/preview")
async def ahrefs_preview(reveal: bool = False):
    creds = credential_store.get("ahrefs")
    if not creds or not creds.get("api_key"):
        return {"value": None, "has_credentials": False}
    key = creds["api_key"]
    return {
        "value": key if reveal else _mask_value(key, 4, 4),
        "has_credentials": True,
    }


@app.get("/api/credentials/ngrok/preview")
async def ngrok_preview(reveal: bool = False):
    creds = credential_store.get("ngrok")
    if not creds or not creds.get("authtoken"):
        return {"value": None, "has_credentials": False}
    token = creds["authtoken"]
    return {
        "value": token if reveal else _mask_ngrok_token(token),
        "has_credentials": True,
    }


@app.post("/api/ahrefs/save-key")
async def ahrefs_save_key(request: Request):
    body = await request.json()
    api_key = body.get("api_key", "").strip()
    if not api_key:
        raise HTTPException(400, "api_key is required")
    credential_store.set("ahrefs", {"api_key": api_key})
    return {"ok": True, "message": "Ahrefs API key saved"}


# ─── API: ngrok ───────────────────────────────────────────────────────────────

@app.post("/api/ngrok/connect")
async def ngrok_connect(request: Request):
    body = await request.json()
    authtoken = body.get("authtoken", "").strip()
    static_domain = body.get("static_domain", "").strip()

    if not authtoken or not static_domain:
        raise HTTPException(400, "authtoken and static_domain are required")

    result = ngrok_manager.connect(authtoken, static_domain)
    if not result["ok"]:
        raise HTTPException(500, result.get("error", "ngrok connection failed"))

    return result


# ─── API: Credentials ─────────────────────────────────────────────────────────

@app.delete("/api/credentials/{service}")
async def delete_credential(service: str):
    if service not in ("gsc", "ga4", "ahrefs", "ngrok"):
        raise HTTPException(400, f"Unknown service: {service}")

    if service == "ngrok":
        ngrok_manager.disconnect()
    else:
        credential_store.delete(service)
        if service in ("gsc", "ga4"):
            _clear_upload_meta(service)

    return {"ok": True, "message": f"{service.upper()} credentials deleted"}


@app.delete("/api/credentials")
async def delete_all_credentials():
    ngrok_manager.disconnect()
    credential_store.delete_all()
    for svc in ("gsc", "ga4"):
        _clear_upload_meta(svc)
    return {"ok": True, "message": "All credentials deleted"}


@app.get("/api/connector-log")
async def connector_log():
    return get_log()


@app.post("/api/connector/stop")
async def connector_stop():
    """Stop ngrok tunnel (keep credentials for reconnect)."""
    result = ngrok_manager.stop_tunnel()
    if not result.get("ok"):
        raise HTTPException(500, result.get("error", "Failed to stop connector"))
    return {"ok": True, "message": "Connector stopped"}


# ─── API: Connect All (Sequential) ───────────────────────────────────────────

@app.post("/api/connect-all")
async def connect_all(request: Request):
    body = await request.json()
    ngrok_authtoken = body.get("ngrok_authtoken", "").strip()
    ngrok_domain = body.get("ngrok_domain", "").strip()

    # ถ้า token เป็นค่าที่ mask ไว้ (มี x ต่อกันหลายตัว เช่น 3ASuxxx...xxx3123) ให้ใช้ credentials ที่เก็บไว้แทน
    if "xxxxxxxx" in ngrok_authtoken and ngrok_authtoken.count("x") >= 8:
        ngrok_creds = credential_store.get("ngrok")
        if ngrok_creds:
            ngrok_authtoken = ngrok_creds.get("authtoken", "") or ""
            ngrok_domain = ngrok_domain or ngrok_creds.get("static_domain", "") or ""

    results: dict[str, Any] = {}

    # 1. GSC
    gsc_test = await gsc_mcp.test_connection()
    results["gsc"] = {"status": "connected" if gsc_test["ok"] else "failed", "message": gsc_test.get("error", "Connected")}
    if gsc_test["ok"]:
        credential_store.set("gsc", credential_store.get("gsc") or {})

    # 2. GA4
    ga4_test = await ga4_mcp.test_connection()
    results["ga4"] = {"status": "connected" if ga4_test["ok"] else "failed", "message": ga4_test.get("error", "Connected")}
    if ga4_test["ok"]:
        credential_store.set("ga4", credential_store.get("ga4") or {})

    # 3. Ahrefs
    ahrefs_test = await ahrefs_mcp.test_connection()
    results["ahrefs"] = {"status": "connected" if ahrefs_test["ok"] else "failed", "message": ahrefs_test.get("error", "Connected")}
    if ahrefs_test["ok"]:
        credential_store.set("ahrefs", credential_store.get("ahrefs") or {})

    # 4. ngrok
    if ngrok_authtoken and ngrok_domain:
        ngrok_result = ngrok_manager.connect(ngrok_authtoken, ngrok_domain)
        if not ngrok_result["ok"]:
            results["ngrok"] = {"status": "failed", "message": ngrok_result.get("error", "ngrok failed")}
            results["mcp_hub"] = {"status": "offline", "message": "ngrok failed — no public URL"}
            return {"ok": False, "results": results, "mcp_url": None}
        results["ngrok"] = {"status": "connected", "mcp_url": ngrok_result.get("mcp_url")}
    else:
        ngrok_creds = credential_store.get("ngrok")
        if ngrok_creds and ngrok_manager.is_connected():
            results["ngrok"] = {"status": "connected", "mcp_url": ngrok_creds.get("mcp_url")}
        elif ngrok_creds and not ngrok_manager.is_connected():
            # Try reconnecting with stored credentials
            stored_token  = ngrok_creds.get("authtoken", "")
            stored_domain = ngrok_creds.get("static_domain", "")
            if stored_token and stored_domain:
                ngrok_result = ngrok_manager.connect(stored_token, stored_domain)
                if ngrok_result["ok"]:
                    results["ngrok"] = {"status": "connected", "mcp_url": ngrok_result.get("mcp_url")}
                else:
                    results["ngrok"] = {"status": "failed", "message": ngrok_result.get("error", "ngrok reconnect failed")}
                    results["mcp_hub"] = {"status": "offline", "message": "ngrok failed — no public URL"}
                    return {"ok": False, "results": results, "mcp_url": None}
            else:
                results["ngrok"] = {"status": "failed", "message": "No ngrok credentials provided"}
                results["mcp_hub"] = {"status": "offline", "message": "ngrok not connected"}
                return {"ok": False, "results": results, "mcp_url": None}
        else:
            results["ngrok"] = {"status": "failed", "message": "No ngrok credentials provided"}
            results["mcp_hub"] = {"status": "offline", "message": "ngrok not connected"}
            return {"ok": False, "results": results, "mcp_url": None}

    # 5. MCP Hub Online
    results["mcp_hub"] = {"status": "online"}
    ngrok_creds = credential_store.get("ngrok")
    mcp_url = ngrok_creds.get("mcp_url") if ngrok_creds else None

    return {"ok": True, "results": results, "mcp_url": mcp_url}


@app.post("/api/refresh")
async def refresh_status():
    """Re-check all service connections."""
    results = {}

    gsc_test = await gsc_mcp.test_connection()
    results["gsc"] = "connected" if gsc_test["ok"] else "failed"
    if not gsc_test["ok"] and credential_store.get("gsc"):
        creds = credential_store.get("gsc")
        creds["status"] = "failed"
        credential_store._write({**credential_store._read(), "gsc": creds})

    ga4_test = await ga4_mcp.test_connection()
    results["ga4"] = "connected" if ga4_test["ok"] else "failed"
    if not ga4_test["ok"] and credential_store.get("ga4"):
        creds = credential_store.get("ga4")
        creds["status"] = "failed"
        credential_store._write({**credential_store._read(), "ga4": creds})

    ahrefs_test = await ahrefs_mcp.test_connection()
    results["ahrefs"] = "connected" if ahrefs_test["ok"] else "failed"
    if not ahrefs_test["ok"] and credential_store.get("ahrefs"):
        creds = credential_store.get("ahrefs")
        creds["status"] = "failed"
        credential_store._write({**credential_store._read(), "ahrefs": creds})

    results["ngrok"] = "connected" if ngrok_manager.is_connected() else "disconnected"
    results["mcp_hub"] = "online" if ngrok_manager.is_connected() else "offline"

    return {"ok": True, "results": results}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mcp-hub"}
