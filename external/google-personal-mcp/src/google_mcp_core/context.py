from typing import List, Optional
from googleapiclient.discovery import build
from .auth import AuthManager


class GoogleContext:
    def __init__(
        self,
        profile: str = "default",
        scopes: Optional[List[str]] = None,
        app_name: str = "google-personal-mcp",
    ):
        self.profile = profile
        self.scopes = scopes or [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        self.auth_manager = AuthManager(app_name=app_name)
        self._creds = None
        self._services = {}

    @property
    def credentials(self):
        if not self._creds:
            self._creds = self.auth_manager.get_credentials(self.profile, self.scopes)
        return self._creds

    def get_service(self, service_name: str, version: str):
        key = (service_name, version)
        if key not in self._services:
            self._services[key] = build(service_name, version, credentials=self.credentials)
        return self._services[key]

    @property
    def sheets(self):
        return self.get_service("sheets", "v4")

    @property
    def drive(self):
        return self.get_service("drive", "v3")
