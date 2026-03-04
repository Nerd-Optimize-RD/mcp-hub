#!/bin/sh
set -e

echo "Starting MCP Hub..."

# Start static UI server on port 8080 (background)
cd /app/ui && python -m http.server 8080 &
UI_PID=$!
echo "UI server started on port 8080 (PID: $UI_PID)"

# Start FastAPI backend on port 8000 (foreground)
cd /app
echo "Starting FastAPI backend on port 8000..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
