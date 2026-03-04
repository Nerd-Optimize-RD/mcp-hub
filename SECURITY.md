# MCP Hub — Security

## Project Structure

```
mcp-hub/
├── main.py              # FastAPI entry, routes
├── connector_log.py     # Connection tracking
├── auth/                # OAuth, credential storage
├── services/            # GSC, GA4, Ahrefs MCP
├── middleware/          # Tool dispatch
├── ngrok/               # Tunnel manager
├── ui/                  # Web UI (static)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

Clear structure with separation of concerns.

---

## Security Practices

**OAuth**
- OAuth state parameter used to prevent CSRF
- Client secret files removed after successful OAuth

**Credentials**
- Credentials not exposed unnecessarily; masked values used where appropriate
- CredentialStore uses proper API; internal methods not called from outside

**API**
- CORS restricted to localhost origins (8080, 8000)
- File upload limit of 100 KB for client_secret.json to reduce DoS risk

**Documentation**
- README includes Security Notice with usage guidelines
- .gitignore excludes sensitive data (credentials, env, data volume)
- DISCLAIMER and LICENSE included

---

*NerdOptimize MCP Hub v1.0*
