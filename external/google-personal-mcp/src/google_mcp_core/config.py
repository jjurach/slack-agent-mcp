import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from google_mcp_core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


def load_env_file(env_path: Optional[str] = None) -> None:
    """
    Load environment variables from .env file.

    Searches common locations if env_path not provided:
    1. ~/.env
    2. ~/.config/google-personal-mcp/.env
    3. .env in current directory

    Supports comments (lines starting with #) and simple KEY=VALUE format.

    Args:
        env_path: Optional explicit path to .env file
    """
    if env_path is None:
        # Try common locations
        candidates = [
            Path.home() / ".env",
            Path.home() / ".config" / "google-personal-mcp" / ".env",
            Path(".env"),
        ]
        for path in candidates:
            if path.exists():
                env_path = str(path)
                break

    if env_path and os.path.exists(env_path):
        logger.debug(f"Loading environment variables from {env_path}")
        try:
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip("'\"")
                            os.environ[key] = value
                            logger.debug(f"Set environment variable: {key}")
        except Exception as e:
            logger.warning(f"Failed to load .env file from {env_path}: {e}")


class ResourceConfig(BaseModel):
    """Configuration for a Google resource (sheet or folder)."""

    id: str
    profile: str = "default"
    description: Optional[str] = None


class RetryConfig(BaseModel):
    """Retry configuration for API calls."""

    enabled: bool = True
    max_retries: int = 3
    backoff_factor: float = 2.0
    initial_delay: float = 1.0


class AuditConfig(BaseModel):
    """Audit logging configuration."""

    enabled: bool = True
    log_path: Optional[str] = None


class AppConfig(BaseModel):
    """Main application configuration."""

    sheets: Dict[str, ResourceConfig] = Field(default_factory=dict)
    drive_folders: Dict[str, ResourceConfig] = Field(default_factory=dict)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    audit_logging: AuditConfig = Field(default_factory=AuditConfig)


class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        # Load .env file before determining config path (allows env var overrides)
        load_env_file()
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()

    def _get_default_config_path(self) -> str:
        """
        Get config path based on environment.

        Priority:
        1. GOOGLE_PERSONAL_MCP_CONFIG env var (explicit path)
        2. ~/.config/google-personal-mcp/config.{ENV}.json (if GOOGLE_MCP_ENV set)
        3. ~/.config/google-personal-mcp/config.json (default)
        """
        # Check explicit config path
        explicit = os.getenv("GOOGLE_PERSONAL_MCP_CONFIG")
        if explicit:
            logger.debug(f"Using explicit config path: {explicit}")
            return explicit

        # Check environment-specific config
        env = os.getenv("GOOGLE_MCP_ENV", "default")
        base_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        env_config = os.path.join(base_dir, "google-personal-mcp", f"config.{env}.json")

        if env != "default" and os.path.exists(env_config):
            logger.debug(f"Found environment-specific config for {env} at {env_config}")
            return env_config

        # Fall back to default
        default_config = os.path.join(base_dir, "google-personal-mcp", "config.json")
        return default_config

    def _load_config(self) -> AppConfig:
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return AppConfig(**data)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in config file {self.config_path}: {e}")
                raise ConfigurationError(f"Invalid JSON in config file: {e}")
            except Exception as e:
                logger.error(f"Failed to load config from {self.config_path}: {e}")
                raise ConfigurationError(f"Failed to load config: {e}")
        else:
            logger.debug(f"Config file not found at {self.config_path}, using defaults")
            return AppConfig()

    def get_sheet_resource(self, alias: str) -> ResourceConfig:
        """Get sheet resource by alias."""
        if alias in self.config.sheets:
            return self.config.sheets[alias]
        raise ConfigurationError(f"Sheet alias '{alias}' not found in configuration.")

    def get_folder_resource(self, alias: str) -> ResourceConfig:
        """Get folder resource by alias."""
        if alias in self.config.drive_folders:
            return self.config.drive_folders[alias]
        raise ConfigurationError(f"Folder alias '{alias}' not found in configuration.")

    def get_allowed_folder_ids(self, profile_name: Optional[str] = None) -> List[str]:
        """Returns folder IDs, optionally filtered by profile."""
        if profile_name:
            return [r.id for r in self.config.drive_folders.values() if r.profile == profile_name]
        return [r.id for r in self.config.drive_folders.values()]

    def list_sheets(self, profile_name: Optional[str] = None) -> Dict[str, ResourceConfig]:
        """Returns configured sheets, optionally filtered by profile."""
        if profile_name:
            return {k: v for k, v in self.config.sheets.items() if v.profile == profile_name}
        return self.config.sheets

    def list_folders(self, profile_name: Optional[str] = None) -> Dict[str, ResourceConfig]:
        """Returns configured drive folders, optionally filtered by profile."""
        if profile_name:
            return {k: v for k, v in self.config.drive_folders.items() if v.profile == profile_name}
        return self.config.drive_folders

    def save_config(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w") as f:
            f.write(self.config.model_dump_json(indent=2))
