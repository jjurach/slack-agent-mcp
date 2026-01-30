import os
import json
import logging
import tempfile
from typing import List
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from google_mcp_core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class AuthManager:
    def __init__(self, app_name: str = "google-personal-mcp"):
        self.app_name = app_name

    def get_config_dir(self, profile: str = "default") -> str:
        """Returns the configuration directory for a given profile."""
        base_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        config_dir = os.path.join(base_dir, self.app_name, "profiles", profile)
        os.makedirs(config_dir, exist_ok=True)
        return config_dir

    def get_credentials_path(self, profile: str = "default") -> str:
        """
        Get the path to credentials.json for a profile.

        Priority:
        1. GOOGLE_PERSONAL_CREDENTIALS_JSON env var (JSON content)
        2. File: ~/.config/google-personal-mcp/profiles/{profile}/credentials.json
        """
        # Check if credentials provided via environment variable (JSON content)
        env_creds = os.getenv("GOOGLE_PERSONAL_CREDENTIALS_JSON")
        if env_creds:
            try:
                # Validate it's valid JSON
                json.loads(env_creds)
                # Write to temp file for InstalledAppFlow.from_client_secrets_file
                temp_file = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False, prefix="credentials_"
                )
                temp_file.write(env_creds)
                temp_file.close()
                logger.debug("Using credentials from GOOGLE_PERSONAL_CREDENTIALS_JSON env var")
                return temp_file.name
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in GOOGLE_PERSONAL_CREDENTIALS_JSON: {e}")
                raise AuthenticationError(f"Invalid credentials JSON: {e}")

        # Otherwise, use file-based approach
        config_dir = self.get_config_dir(profile)
        path = os.path.join(config_dir, "credentials.json")

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"credentials.json not found for profile '{profile}'.\n"
                f"Expected location: {path}\n"
                f"Place your OAuth 2.0 credentials file there and try again."
            )
        logger.debug(f"Using credentials from file: {path}")
        return path

    def get_token_path(self, profile: str = "default") -> str:
        """
        Get the path to token.json for a profile.

        Priority:
        1. GOOGLE_PERSONAL_TOKEN_JSON env var (JSON content)
        2. File: ~/.config/google-personal-mcp/profiles/{profile}/token.json
        """
        # Check if token provided via environment variable
        env_token = os.getenv("GOOGLE_PERSONAL_TOKEN_JSON")
        if env_token:
            try:
                # Validate it's valid JSON
                json.loads(env_token)
                # Write to temp file for token loading
                temp_file = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False, prefix="token_"
                )
                temp_file.write(env_token)
                temp_file.close()
                logger.debug("Using token from GOOGLE_PERSONAL_TOKEN_JSON env var")
                return temp_file.name
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in GOOGLE_PERSONAL_TOKEN_JSON: {e}")
                raise AuthenticationError(f"Invalid token JSON: {e}")

        # Otherwise, use file-based approach
        config_dir = self.get_config_dir(profile)
        return os.path.join(config_dir, "token.json")

    def get_credentials(self, profile: str = "default", scopes: List[str] = None) -> Credentials:
        """
        Get Google API credentials for the given profile and scopes.

        Args:
            profile: Profile name (default: "default")
            scopes: List of OAuth scopes to request

        Returns:
            google.oauth2.credentials.Credentials object

        Raises:
            AuthenticationError: If authentication fails
            FileNotFoundError: If credentials.json is not found
        """
        if scopes is None:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]

        try:
            token_path = self.get_token_path(profile)
        except Exception as e:
            raise AuthenticationError(f"Failed to get token path: {e}")

        creds = None
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path)
                if creds and not creds.has_scopes(scopes):
                    logger.info(
                        f"Token exists but lacks required scopes. Re-authenticating for profile '{profile}'..."
                    )
                    creds = None
            except Exception as e:
                logger.warning(f"Failed to load token from {token_path}: {e}")
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.debug(f"Refreshing token for profile '{profile}'...")
                    creds.refresh(GoogleRequest())
                    logger.info(f"Token refreshed successfully for profile '{profile}'")
                except Exception as e:
                    logger.warning(f"Failed to refresh token: {e}. Will re-authenticate.")
                    creds = None

            if not creds:
                logger.info(f"Starting OAuth2 authentication for profile '{profile}'...")
                try:
                    credentials_path = self.get_credentials_path(profile)
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
                    creds = flow.run_local_server(port=0)
                    logger.info(f"OAuth2 authentication completed for profile '{profile}'")
                except Exception as e:
                    raise AuthenticationError(
                        f"OAuth2 authentication failed for profile '{profile}': {e}"
                    )

            # Save token to profile directory
            try:
                # Only save if not from env var (env var tokens are temporary)
                if not os.getenv("GOOGLE_PERSONAL_TOKEN_JSON"):
                    with open(token_path, "w") as f:
                        f.write(creds.to_json())
                    logger.info(f"Authorization token saved to: {token_path}")
            except Exception as e:
                logger.warning(f"Failed to save token: {e}")

        return creds
