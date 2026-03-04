# MCP Hub

> Single Docker container รวม GSC + GA4 + Ahrefs MCP พร้อม Web UI สำหรับ Setup

**Powered by NerdOptimize — https://nerdoptimize.com**

---

## Quick Start

### ต้องการ
- Docker Desktop
- ngrok account (free tier) — https://ngrok.com
- Google Cloud Console project พร้อม OAuth credentials
- Ahrefs API key (optional)

---

## วิธีติดตั้ง

### 1. Build & Run
```bash
docker compose up --build -d
```

### 2. เปิด Setup Panel
เปิด browser ไปที่ → **http://localhost:8080**

### 3. ตั้งค่าทีละ service

#### Google Search Console (GSC)
1. ไปที่ [Google Cloud Console](https://console.cloud.google.com)
2. สร้าง OAuth 2.0 Client ID → ประเภท "Desktop app"
3. เพิ่ม `http://localhost:8000/api/oauth/callback` ใน Authorized redirect URIs
4. Download `client_secret.json`
5. Upload ที่ Setup Panel → กด **Connect Google Account — GSC**
6. Login Google และ grant permission

#### Google Analytics 4 (GA4)
เหมือน GSC แต่ใช้ OAuth credentials คนละตัวได้ (หรือตัวเดียวกัน)
1. เปิด Google Analytics Data API ใน Cloud Console
2. Upload `client_secret.json` สำหรับ GA4
3. กด **Connect Google Account — GA4**

#### Ahrefs
1. ไปที่ https://app.ahrefs.com/api
2. Copy API key
3. วาง API key ในช่อง Ahrefs → กด **Save**

#### ngrok
1. ไปที่ https://dashboard.ngrok.com
2. Copy authtoken ของคุณ
3. สร้าง Static Domain (free tier ได้ 1 อัน)
4. วาง Auth Token + Static Domain ใน Setup Panel

### 4. กด Connect & Start MCP Hub
ระบบจะ:
1. ตรวจสอบ GSC credentials
2. ตรวจสอบ GA4 credentials
3. ทดสอบ Ahrefs API Key
4. เชื่อมต่อ ngrok tunnel
5. เปิด MCP Hub → แสดง URL

### 5. Copy MCP URL
Copy URL จาก Setup Panel เพื่อต่อกับ Claude หรือ ChatGPT

---

## การเชื่อมต่อกับ Claude

1. ไปที่ Claude.ai → Settings → Integrations
2. เพิ่ม MCP URL: `https://your-domain.ngrok-free.app/mcp-hub/sse`
3. Claude จะสามารถใช้ tools ทั้งหมดที่ connect แล้วได้ทันที

---

## MCP Tools ที่มี

### Google Search Console
- `list_sites` — list ทุก property
- `get_search_analytics` — ดึง clicks, impressions, CTR, position

### Google Analytics 4
- `list_ga4_properties` — list ทุก GA4 property **(เริ่มที่นี่เสมอ)**
- `get_recommended_analytics` — ภาพรวม analytics
- `get_top_pages` — หน้าที่มี traffic สูงสุด
- `get_traffic_sources` — แหล่งที่มา traffic
- `get_device_breakdown` — แบ่งตาม device
- `get_conversion_report` — conversion / key events
- `get_realtime_data` — real-time visitors
- `compare_date_ranges` — เปรียบเทียบ 2 ช่วงเวลา
- และอีก 10+ tools

### Ahrefs
- `get_domain_rating` — DR score
- `get_backlinks` — รายการ backlinks
- `get_referring_domains` — referring domains
- `get_organic_keywords` — organic keywords
- `get_top_pages` — top pages by traffic
- `get_competitors` — competing domains
- `get_keyword_difficulty` — keyword difficulty + volume

---

## Ports

| Port | Service |
|------|---------|
| 8080 | Web UI Setup Panel |
| 8000 | FastAPI Backend + MCP endpoint + OAuth callback |

---

## Credential Storage

Credentials เก็บใน Docker Volume ที่ `/data/credentials.json`
- ปิด/เปิด container → credentials ยังอยู่
- ลบได้ผ่าน Setup Panel (Disconnect รายตัว หรือ Delete All)

---

## Troubleshooting

**OAuth popup ไม่เปิด**
→ Allow popups สำหรับ http://localhost:8080 ใน browser

**ngrok connection failed**
→ ตรวจสอบ authtoken ถูกต้อง และ static domain ตรงกับที่ตั้งใน ngrok dashboard

**GSC/GA4 Failed after connect**
→ ตรวจสอบว่า Google Cloud project มี API ที่ต้องการเปิดใช้งานแล้ว

---

*Powered by NerdOptimize © 2026 — https://nerdoptimize.com*
