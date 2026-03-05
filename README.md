# MCP Hub

> Single Docker container that combines GSC, GA4, and Ahrefs MCP with a Web UI for setup.

**Powered by NerdOptimize — https://nerdoptimize.com**

---

## Quick Start

### Prerequisites
- Docker Desktop
- ngrok account (free tier) — https://ngrok.com
- Google Cloud Console project with OAuth credentials
- Ahrefs API key (optional)

---

## Installation

### 1. Build & Run
```bash
docker compose up --build -d
```

### 2. Open Setup Panel
Open your browser at → **http://localhost:8080**

### 3. Configure each service

#### Google Search Console (GSC)
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create OAuth 2.0 Client ID → type "Desktop app"
3. Add `http://localhost:8000/api/oauth/callback` to Authorized redirect URIs
4. Download `client_secret.json`
5. Upload in Setup Panel → click **Connect Google Account — GSC**
6. Log in with Google and grant permission

#### Google Analytics 4 (GA4)
Similar to GSC — you can use separate OAuth credentials or the same one.
1. Enable Google Analytics Data API in Cloud Console
2. Upload `client_secret.json` for GA4
3. Click **Connect Google Account — GA4**

#### Ahrefs
1. Go to https://app.ahrefs.com/api
2. Copy your API key
3. Paste the API key in the Ahrefs field → click **Save**

#### ngrok
1. Go to https://dashboard.ngrok.com
2. Copy your authtoken
3. Create a Static Domain (1 free on free tier)
4. Paste Auth Token + Static Domain in the Setup Panel

### 4. Click Connect & Start MCP Hub
The system will:
1. Verify GSC credentials
2. Verify GA4 credentials
3. Test Ahrefs API key
4. Connect ngrok tunnel
5. Start MCP Hub → display the URL

### 5. Copy MCP URL
Copy the URL from the Setup Panel to connect with Claude or ChatGPT

---

## Connecting to Claude

1. Go to Claude.ai → Settings → Integrations
2. Add MCP URL: `https://your-domain.ngrok-free.app/mcp-hub/sse`
3. Claude can use all connected tools immediately

---

## Available MCP Tools

### Google Search Console
- `list_sites` — list all properties
- `get_search_analytics` — get clicks, impressions, CTR, position (supports web, image, video, news, discover, googleNews)
- `inspect_url` — inspect a URL's index status in Google
- `get_site` — get property details
- `list_sitemaps` — list submitted sitemaps
- `get_sitemap` — get sitemap details
- `submit_sitemap` — submit a sitemap
- `delete_sitemap` — delete a sitemap

### Google Analytics 4
- `list_ga4_properties` — list all GA4 properties **(start here)**
- `get_recommended_analytics` — analytics overview
- `get_top_pages` — top pages by traffic
- `get_traffic_sources` — traffic sources
- `get_device_breakdown` — breakdown by device
- `get_conversion_report` — conversions / key events
- `get_realtime_data` — real-time visitors
- `compare_date_ranges` — compare two date ranges
- and 10+ more tools

### Ahrefs
- `get_domain_rating` — DR score
- `get_backlinks` — backlink list
- `get_referring_domains` — referring domains
- `get_organic_keywords` — organic keywords
- `get_top_pages` — top pages by traffic
- `get_competitors` — competing domains
- `get_keyword_difficulty` — keyword difficulty + volume

---

## Security Notice

**MCP Hub Setup Panel has no authentication.** It is designed for **local use only**.

- ✅ Use only on `localhost` — do not expose port 8080 or 8000 to the internet
- ✅ When using ngrok, the MCP endpoint (`/mcp-hub/sse`) is public for AI clients — the Setup Panel should only be accessed from your machine
- ⚠️ Do not open the Setup Panel (port 8080) through ngrok or any public URL

---

## Ports

| Port | Service |
|------|---------|
| 8080 | Web UI Setup Panel |
| 8000 | FastAPI Backend + MCP endpoint + OAuth callback |

---

## Credential Storage

Credentials are stored in the Docker volume at `/data/credentials.json`
- Stopping or restarting the container preserves credentials
- Remove via Setup Panel (Disconnect per service or Delete All)

---

## Troubleshooting

**OAuth popup does not open**
→ Allow popups for http://localhost:8080 in your browser

**ngrok connection failed**
→ Verify authtoken is correct and static domain matches your ngrok dashboard

**GSC/GA4 Failed after connect**
→ Ensure your Google Cloud project has the required APIs enabled

---

*Powered by NerdOptimize © 2026 — https://nerdoptimize.com*
