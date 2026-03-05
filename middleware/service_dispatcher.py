"""
Service Dispatcher — routes MCP tool calls to the appropriate service.
NerdOptimize
"""
from __future__ import annotations

from services import gsc_mcp, ga4_mcp, ahrefs_mcp

# Map tool name → (service_module, async_function)
TOOL_REGISTRY: dict[str, tuple] = {
    # GSC tools
    "list_sites": (gsc_mcp, gsc_mcp.list_sites),
    "get_search_analytics": (gsc_mcp, gsc_mcp.get_search_analytics),
    "inspect_url": (gsc_mcp, gsc_mcp.inspect_url),
    "get_site": (gsc_mcp, gsc_mcp.get_site),
    "list_sitemaps": (gsc_mcp, gsc_mcp.list_sitemaps),
    "get_sitemap": (gsc_mcp, gsc_mcp.get_sitemap),
    "submit_sitemap": (gsc_mcp, gsc_mcp.submit_sitemap),
    "delete_sitemap": (gsc_mcp, gsc_mcp.delete_sitemap),
    # GA4 tools
    "list_ga4_properties": (ga4_mcp, ga4_mcp.list_ga4_properties),
    "get_recommended_analytics": (ga4_mcp, ga4_mcp.get_recommended_analytics),
    "get_ga4_data": (ga4_mcp, ga4_mcp.get_ga4_data),
    "get_top_pages_ga4": (ga4_mcp, ga4_mcp.get_top_pages),
    "get_traffic_sources": (ga4_mcp, ga4_mcp.get_traffic_sources),
    "get_device_breakdown": (ga4_mcp, ga4_mcp.get_device_breakdown),
    "get_conversion_report": (ga4_mcp, ga4_mcp.get_conversion_report),
    "get_audience_report": (ga4_mcp, ga4_mcp.get_audience_report),
    "get_realtime_data": (ga4_mcp, ga4_mcp.get_realtime_data),
    "get_realtime_active_users": (ga4_mcp, ga4_mcp.get_realtime_active_users),
    "compare_date_ranges": (ga4_mcp, ga4_mcp.compare_date_ranges),
    "run_funnel_report": (ga4_mcp, ga4_mcp.run_funnel_report),
    "search_schema": (ga4_mcp, ga4_mcp.search_schema),
    "list_dimension_categories": (ga4_mcp, ga4_mcp.list_dimension_categories),
    "list_metric_categories": (ga4_mcp, ga4_mcp.list_metric_categories),
    "get_dimensions_by_category": (ga4_mcp, ga4_mcp.get_dimensions_by_category),
    "get_metrics_by_category": (ga4_mcp, ga4_mcp.get_metrics_by_category),
    # Ahrefs tools
    "get_domain_rating": (ahrefs_mcp, ahrefs_mcp.get_domain_rating),
    "get_backlinks": (ahrefs_mcp, ahrefs_mcp.get_backlinks),
    "get_referring_domains": (ahrefs_mcp, ahrefs_mcp.get_referring_domains),
    "get_organic_keywords": (ahrefs_mcp, ahrefs_mcp.get_organic_keywords),
    "get_top_pages": (ahrefs_mcp, ahrefs_mcp.get_top_pages),
    "get_competitors": (ahrefs_mcp, ahrefs_mcp.get_competitors),
    "get_keyword_difficulty": (ahrefs_mcp, ahrefs_mcp.get_keyword_difficulty),
    "list_ahrefs_projects": (ahrefs_mcp, ahrefs_mcp.list_ahrefs_projects),
    "list_site_audit_projects": (ahrefs_mcp, ahrefs_mcp.list_site_audit_projects),
    "list_site_audit_issues": (ahrefs_mcp, ahrefs_mcp.list_site_audit_issues),
    "list_anchors": (ahrefs_mcp, ahrefs_mcp.list_anchors),
    "get_pages_by_traffic": (ahrefs_mcp, ahrefs_mcp.get_pages_by_traffic),
    "get_subscription_limits": (ahrefs_mcp, ahrefs_mcp.get_subscription_limits),
}

# Which service each tool belongs to (for availability checks)
TOOL_SERVICE_MAP: dict[str, str] = {
    "list_sites": "gsc",
    "get_search_analytics": "gsc",
    "inspect_url": "gsc",
    "get_site": "gsc",
    "list_sitemaps": "gsc",
    "get_sitemap": "gsc",
    "submit_sitemap": "gsc",
    "delete_sitemap": "gsc",
    "list_ga4_properties": "ga4",
    "get_recommended_analytics": "ga4",
    "get_ga4_data": "ga4",
    "get_top_pages_ga4": "ga4",
    "get_traffic_sources": "ga4",
    "get_device_breakdown": "ga4",
    "get_conversion_report": "ga4",
    "get_audience_report": "ga4",
    "get_realtime_data": "ga4",
    "get_realtime_active_users": "ga4",
    "compare_date_ranges": "ga4",
    "run_funnel_report": "ga4",
    "search_schema": "ga4",
    "list_dimension_categories": "ga4",
    "list_metric_categories": "ga4",
    "get_dimensions_by_category": "ga4",
    "get_metrics_by_category": "ga4",
    "get_domain_rating": "ahrefs",
    "get_backlinks": "ahrefs",
    "get_referring_domains": "ahrefs",
    "get_organic_keywords": "ahrefs",
    "get_top_pages": "ahrefs",
    "get_competitors": "ahrefs",
    "get_keyword_difficulty": "ahrefs",
    "list_ahrefs_projects": "ahrefs",
    "list_site_audit_projects": "ahrefs",
    "list_site_audit_issues": "ahrefs",
    "list_anchors": "ahrefs",
    "get_pages_by_traffic": "ahrefs",
    "get_subscription_limits": "ahrefs",
}


async def dispatch(tool_name: str, arguments: dict) -> str:
    """Route a tool call to the appropriate MCP service handler."""
    if tool_name not in TOOL_REGISTRY:
        return f'{{"error": "Unknown tool: {tool_name}"}}'

    _, handler = TOOL_REGISTRY[tool_name]
    return await handler(**arguments)
