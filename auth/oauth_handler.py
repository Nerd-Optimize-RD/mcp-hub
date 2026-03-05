import json
import os
import tempfile

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from auth.credential_store import CredentialStore

SCOPES = {
    "gsc": ["https://www.googleapis.com/auth/webmasters"],
    "ga4": ["https://www.googleapis.com/auth/analytics.readonly"],
}

# Use port 8000 (FastAPI) for callback - more reliable than separate server on 8085
REDIRECT_URI_BASE = "http://localhost:8000"
REDIRECT_URI = f"{REDIRECT_URI_BASE}/api/oauth/callback"

# Global state for pending OAuth flows (state -> service)
_pending_flows: dict[str, dict] = {}
_pending_by_state: dict[str, str] = {}  # state -> service
_oauth_results: dict[str, dict] = {}


def _success_page(service: str) -> str:
    return f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<style>
  body {{ background: #1d262e; color: #fff; font-family: monospace;
         display: flex; align-items: center; justify-content: center;
         min-height: 100vh; margin: 0; }}
  .box {{ background: #2c3a47; border: 1px solid #2ecc71; border-radius: 12px;
          padding: 40px; text-align: center; max-width: 400px; }}
  h2 {{ color: #2ecc71; margin-bottom: 12px; }}
  p {{ color: #8a9bb0; font-size: 14px; }}
</style></head>
<body><div class="box">
  <h2>✅ Connected!</h2>
  <p>{service.upper()} connected successfully.</p>
  <p style="margin-top:16px;font-size:12px;">You can close this window.</p>
</div></body></html>"""


def _error_page(error: str) -> str:
    return f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<style>
  body {{ background: #1d262e; color: #fff; font-family: monospace;
         display: flex; align-items: center; justify-content: center;
         min-height: 100vh; margin: 0; }}
  .box {{ background: #2c3a47; border: 1px solid #e74c3c; border-radius: 12px;
          padding: 40px; text-align: center; max-width: 400px; }}
  h2 {{ color: #e74c3c; margin-bottom: 12px; }}
  p {{ color: #8a9bb0; font-size: 13px; word-break: break-all; }}
</style></head>
<body><div class="box">
  <h2>❌ OAuth Failed</h2>
  <p>{error}</p>
  <p style="margin-top:16px;font-size:12px;">Please close this window and try again.</p>
</div></body></html>"""


def handle_callback(code: str | None, state: str | None, error: str | None) -> tuple[str, int]:
    """
    Handle OAuth callback. Returns (html_content, status_code).
    Called from FastAPI route.
    """
    if error:
        service = _pending_by_state.get(state or "") if state else None
        if service:
            _oauth_results[service] = {"success": False, "error": error}
        return _error_page(error), 200

    if not state or not code:
        return _error_page("Invalid callback — missing code or state"), 400

    service = _pending_by_state.get(state)
    if not service:
        return _error_page("Invalid or expired OAuth session. Please try again."), 400

    flow_data = _pending_flows.get(service)
    if not flow_data:
        return _error_page("OAuth session expired. Please try again."), 400

    try:
        flow: Flow = flow_data["flow"]
        flow.fetch_token(code=code)
        creds: Credentials = flow.credentials

        _oauth_results[service] = {
            "success": True,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "refresh_token": creds.refresh_token,
            "token": creds.token,
        }

        return _success_page(service), 200

    except Exception as e:
        _oauth_results[service] = {"success": False, "error": str(e)}
        return _error_page(str(e)), 200


class OAuthHandler:
    def __init__(self, credential_store: CredentialStore):
        self.store = credential_store

    def start_oauth(self, service: str, client_secret_json: str) -> str:
        """
        Creates the OAuth URL and starts listening for callback.
        Returns the authorization URL for the frontend to open in a popup.
        """
        if service not in SCOPES:
            raise ValueError(f"Unknown service: {service}")

        secret_data = json.loads(client_secret_json)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(secret_data, f)
            tmp_path = f.name

        try:
            flow = Flow.from_client_secrets_file(
                tmp_path,
                scopes=SCOPES[service],
                redirect_uri=REDIRECT_URI,
            )
            auth_url, state = flow.authorization_url(
                access_type="offline",
                prompt="consent",
            )

            _pending_flows[service] = {"flow": flow, "state": state}
            _pending_by_state[state] = service
            _oauth_results.pop(service, None)

            return auth_url

        finally:
            os.unlink(tmp_path)

    def get_oauth_result(self, service: str) -> dict | None:
        """Polls for OAuth result after callback."""
        result = _oauth_results.get(service)
        if result and result.get("success"):
            self.store.set(
                service,
                {
                    "client_id": result["client_id"],
                    "client_secret": result["client_secret"],
                    "refresh_token": result["refresh_token"],
                },
            )
            _oauth_results.pop(service, None)
            flow_data = _pending_flows.pop(service, None)
            if flow_data:
                _pending_by_state.pop(flow_data.get("state"), None)
            # Delete temp client_secret file only after successful OAuth
            try:
                os.unlink(f"/tmp/client_secret_{service}.json")
            except Exception:
                pass
            return {"success": True}
        return result

    def get_credentials(self, service: str) -> Credentials | None:
        """Build a Credentials object from stored credentials."""
        creds_data = self.store.get(service)
        if not creds_data:
            return None

        creds_data_copy = dict(creds_data)
        creds_data_copy.pop("connected_at", None)
        creds_data_copy.pop("status", None)

        return Credentials(
            token=None,
            refresh_token=creds_data_copy.get("refresh_token"),
            client_id=creds_data_copy.get("client_id"),
            client_secret=creds_data_copy.get("client_secret"),
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES.get(service, []),
        )
