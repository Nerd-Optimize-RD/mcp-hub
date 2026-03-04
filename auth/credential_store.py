import json
import os
from datetime import datetime, timezone
from typing import Any, Optional


class CredentialStore:
    def __init__(self, path: str = "/data/credentials.json"):
        self.path = path
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._write({})

    def _read(self) -> dict:
        try:
            with open(self.path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write(self, data: dict):
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)

    def get(self, service: str) -> Optional[dict]:
        return self._read().get(service)

    def set(self, service: str, data: dict):
        all_creds = self._read()
        all_creds[service] = {
            **data,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "status": "connected",
        }
        self._write(all_creds)

    def delete(self, service: str):
        all_creds = self._read()
        all_creds.pop(service, None)
        self._write(all_creds)

    def delete_all(self):
        self._write({})

    def get_all(self) -> dict:
        return self._read()

    def has_service(self, service: str) -> bool:
        creds = self.get(service)
        return creds is not None and creds.get("status") == "connected"
