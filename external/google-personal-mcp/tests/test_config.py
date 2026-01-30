"""Tests for configuration management."""

import os
import json
import pytest

from google_mcp_core.config import (
    load_env_file,
    ConfigManager,
    ResourceConfig,
)
from google_mcp_core.exceptions import ConfigurationError


class TestLoadEnvFile:
    """Test .env file loading functionality."""

    def test_load_env_file_basic(self, tmp_path):
        """Test loading basic .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\nANOTHER_VAR=another_value\n")

        # Clear any existing vars
        os.environ.pop("TEST_VAR", None)
        os.environ.pop("ANOTHER_VAR", None)

        load_env_file(str(env_file))

        assert os.environ.get("TEST_VAR") == "test_value"
        assert os.environ.get("ANOTHER_VAR") == "another_value"

    def test_load_env_file_with_comments(self, tmp_path):
        """Test that comments are ignored."""
        env_file = tmp_path / ".env"
        env_file.write_text("# This is a comment\nVAR=value\n# Another comment\n")

        os.environ.pop("VAR", None)
        load_env_file(str(env_file))

        assert os.environ.get("VAR") == "value"

    def test_load_env_file_with_quoted_values(self, tmp_path):
        """Test handling of quoted values."""
        env_file = tmp_path / ".env"
        env_file.write_text("VAR1=\"double quoted\"\nVAR2='single quoted'\n")

        os.environ.pop("VAR1", None)
        os.environ.pop("VAR2", None)

        load_env_file(str(env_file))

        assert os.environ.get("VAR1") == "double quoted"
        assert os.environ.get("VAR2") == "single quoted"

    def test_load_env_file_nonexistent(self):
        """Test handling of nonexistent file."""
        # Should not raise, just silently skip
        load_env_file("/nonexistent/path/.env")

    def test_load_env_file_with_equals_in_value(self, tmp_path):
        """Test values containing equals signs."""
        env_file = tmp_path / ".env"
        env_file.write_text('JSON_VAR={"key":"value"}\n')

        os.environ.pop("JSON_VAR", None)
        load_env_file(str(env_file))

        assert os.environ.get("JSON_VAR") == '{"key":"value"}'

    def test_load_env_file_empty_lines(self, tmp_path):
        """Test handling of empty lines."""
        env_file = tmp_path / ".env"
        env_file.write_text("\n\nVAR=value\n\n")

        os.environ.pop("VAR", None)
        load_env_file(str(env_file))

        assert os.environ.get("VAR") == "value"


class TestConfigPathResolution:
    """Test configuration path resolution logic."""

    def test_explicit_config_path_env_var(self, tmp_path, monkeypatch):
        """Test GOOGLE_PERSONAL_MCP_CONFIG takes priority."""
        config_file = tmp_path / "explicit_config.json"
        config_file.write_text('{"sheets": {}, "drive_folders": {}}')

        monkeypatch.setenv("GOOGLE_PERSONAL_MCP_CONFIG", str(config_file))
        monkeypatch.delenv("GOOGLE_MCP_ENV", raising=False)

        manager = ConfigManager()
        assert manager.config_path == str(config_file)

    def test_environment_specific_config(self, tmp_path, monkeypatch):
        """Test environment-specific config loading."""
        base_dir = tmp_path / ".config" / "google-personal-mcp"
        base_dir.mkdir(parents=True)

        # Create both default and env-specific configs
        default_config = base_dir / "config.json"
        default_config.write_text('{"sheets": {"default": {"id": "default_id"}}}')

        prod_config = base_dir / "config.prod.json"
        prod_config.write_text('{"sheets": {"prod": {"id": "prod_id"}}}')

        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
        monkeypatch.setenv("GOOGLE_MCP_ENV", "prod")
        monkeypatch.delenv("GOOGLE_PERSONAL_MCP_CONFIG", raising=False)

        manager = ConfigManager()
        assert str(prod_config) in manager.config_path or "config.prod.json" in manager.config_path
        # Verify prod config is loaded
        assert "prod" in manager.config.sheets

    def test_default_config_fallback(self, tmp_path, monkeypatch):
        """Test fallback to default config."""
        base_dir = tmp_path / ".config" / "google-personal-mcp"
        base_dir.mkdir(parents=True)

        default_config = base_dir / "config.json"
        default_config.write_text('{"sheets": {}}')

        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
        monkeypatch.delenv("GOOGLE_MCP_ENV", raising=False)
        monkeypatch.delenv("GOOGLE_PERSONAL_MCP_CONFIG", raising=False)

        manager = ConfigManager()
        assert "config.json" in manager.config_path

    def test_config_priority_order(self, tmp_path, monkeypatch):
        """Test that explicit config takes priority over env-specific."""
        base_dir = tmp_path / ".config" / "google-personal-mcp"
        base_dir.mkdir(parents=True)

        default_config = base_dir / "config.json"
        default_config.write_text('{"sheets": {}}')

        prod_config = base_dir / "config.prod.json"
        prod_config.write_text('{"sheets": {}}')

        explicit_config = tmp_path / "explicit.json"
        explicit_config.write_text('{"sheets": {}}')

        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
        monkeypatch.setenv("GOOGLE_MCP_ENV", "prod")
        monkeypatch.setenv("GOOGLE_PERSONAL_MCP_CONFIG", str(explicit_config))

        manager = ConfigManager()
        assert manager.config_path == str(explicit_config)


class TestConfigManager:
    """Test ConfigManager loading and access."""

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid configuration file."""
        config_file = tmp_path / "config.json"
        config_data = {
            "sheets": {"prompts": {"id": "sheet_123", "profile": "default"}},
            "drive_folders": {},
        }
        config_file.write_text(json.dumps(config_data))

        manager = ConfigManager(str(config_file))
        assert "prompts" in manager.config.sheets
        assert manager.config.sheets["prompts"].id == "sheet_123"

    def test_load_nonexistent_config_returns_defaults(self, tmp_path):
        """Test that missing config returns default AppConfig."""
        nonexistent = tmp_path / "nonexistent.json"
        manager = ConfigManager(str(nonexistent))

        assert manager.config is not None
        assert manager.config.sheets == {}
        assert manager.config.drive_folders == {}

    def test_invalid_json_raises_error(self, tmp_path):
        """Test that invalid JSON raises ConfigurationError."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{invalid json}")

        with pytest.raises(ConfigurationError):
            ConfigManager(str(config_file))

    def test_get_sheet_resource(self, tmp_path):
        """Test retrieving sheet resource by alias."""
        config_file = tmp_path / "config.json"
        config_data = {
            "sheets": {"prompts": {"id": "sheet_123", "profile": "default"}},
            "drive_folders": {},
        }
        config_file.write_text(json.dumps(config_data))

        manager = ConfigManager(str(config_file))
        resource = manager.get_sheet_resource("prompts")

        assert resource.id == "sheet_123"
        assert resource.profile == "default"

    def test_get_nonexistent_sheet_raises_error(self, tmp_path):
        """Test that requesting nonexistent sheet raises error."""
        config_file = tmp_path / "config.json"
        config_data = {"sheets": {}, "drive_folders": {}}
        config_file.write_text(json.dumps(config_data))

        manager = ConfigManager(str(config_file))

        with pytest.raises(ConfigurationError):
            manager.get_sheet_resource("nonexistent")

    def test_list_sheets_all(self, tmp_path):
        """Test listing all sheets."""
        config_file = tmp_path / "config.json"
        config_data = {
            "sheets": {
                "sheet1": {"id": "id1", "profile": "default"},
                "sheet2": {"id": "id2", "profile": "prod"},
            },
            "drive_folders": {},
        }
        config_file.write_text(json.dumps(config_data))

        manager = ConfigManager(str(config_file))
        sheets = manager.list_sheets()

        assert len(sheets) == 2
        assert "sheet1" in sheets
        assert "sheet2" in sheets

    def test_list_sheets_by_profile(self, tmp_path):
        """Test filtering sheets by profile."""
        config_file = tmp_path / "config.json"
        config_data = {
            "sheets": {
                "default_sheet": {"id": "id1", "profile": "default"},
                "prod_sheet": {"id": "id2", "profile": "prod"},
            },
            "drive_folders": {},
        }
        config_file.write_text(json.dumps(config_data))

        manager = ConfigManager(str(config_file))
        sheets = manager.list_sheets(profile_name="default")

        assert len(sheets) == 1
        assert "default_sheet" in sheets
        assert "prod_sheet" not in sheets

    def test_save_config(self, tmp_path):
        """Test saving configuration to file."""
        config_file = tmp_path / "config.json"

        manager = ConfigManager(str(config_file))
        manager.config.sheets["new_sheet"] = ResourceConfig(id="new_id")
        manager.save_config()

        # Reload and verify
        manager2 = ConfigManager(str(config_file))
        assert "new_sheet" in manager2.config.sheets
        assert manager2.config.sheets["new_sheet"].id == "new_id"
