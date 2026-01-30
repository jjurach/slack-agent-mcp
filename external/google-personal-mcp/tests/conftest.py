"""Shared pytest fixtures and configuration."""

import pytest
import json
import tempfile
from pathlib import Path


@pytest.fixture
def temp_config_dir():
    """Temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_config(temp_config_dir):
    """Sample configuration for testing."""
    config = {
        "sheets": {
            "test_sheet": {
                "id": "test_sheet_id_123",
                "profile": "default",
                "description": "Test sheet",
            }
        },
        "drive_folders": {
            "test_folder": {
                "id": "test_folder_id_456",
                "profile": "default",
                "description": "Test folder",
            }
        },
        "retry": {"enabled": True, "max_retries": 3, "backoff_factor": 2.0, "initial_delay": 1.0},
        "audit_logging": {"enabled": True},
    }
    config_path = Path(temp_config_dir) / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)
    return config_path, config


@pytest.fixture
def mock_google_context(mocker):
    """Mock GoogleContext for testing."""
    mock_context = mocker.Mock()
    mock_context.sheets = mocker.Mock()
    mock_context.drive = mocker.Mock()
    mock_context.credentials = mocker.Mock()
    return mock_context


@pytest.fixture
def mock_sheets_service(mocker):
    """Mock SheetsService for testing."""
    mock_service = mocker.Mock()
    mock_service.list_sheet_titles = mocker.Mock(return_value=["Sheet1", "Sheet2"])
    mock_service.read_range = mocker.Mock(return_value=[["A1", "B1"], ["A2", "B2"]])
    mock_service.write_range = mocker.Mock(return_value={"updates": {"updatedCells": 1}})
    mock_service.create_sheet = mocker.Mock(return_value={"spreadsheetId": "test_id"})
    return mock_service


@pytest.fixture
def mock_drive_service(mocker):
    """Mock DriveService for testing."""
    mock_service = mocker.Mock()
    mock_service.list_files = mocker.Mock(
        return_value=[
            {"id": "file1", "name": "File 1", "mimeType": "text/plain"},
            {"id": "file2", "name": "File 2", "mimeType": "text/plain"},
        ]
    )
    mock_service.upload_file = mocker.Mock(return_value={"id": "new_file_id"})
    mock_service.download_file = mocker.Mock()
    mock_service.remove_file = mocker.Mock()
    return mock_service


@pytest.fixture
def mock_config_manager(mocker):
    """Mock ConfigManager for testing."""
    mock_manager = mocker.Mock()
    mock_manager.list_sheets = mocker.Mock(
        return_value={"test": {"id": "test_id", "profile": "default"}}
    )
    mock_manager.list_folders = mocker.Mock(
        return_value={"test": {"id": "test_folder_id", "profile": "default"}}
    )
    return mock_manager
