import os
import logging
from typing import Optional, Tuple, Dict, Any
from mcp.server import FastMCP
from datetime import datetime

from google_mcp_core.context import GoogleContext
from google_mcp_core.sheets import SheetsService
from google_mcp_core.drive import DriveService
from google_mcp_core.config import ConfigManager
from google_mcp_core.logging.structured import setup_structured_logging
from google_mcp_core.logging.audit import AuditLogger
from google_mcp_core.utils.context import set_request_id, clear_request_id
from google_mcp_core.utils.sanitizer import mask_credentials, should_sanitize

# Setup structured logging
VERBOSE = os.getenv("GOOGLE_PERSONAL_MCP_VERBOSE", "").lower() in ("1", "true", "yes")
setup_structured_logging(verbose=VERBOSE)
logger = logging.getLogger(__name__)

# Initialize Config
config_manager = ConfigManager()

# Initialize Audit Logger
audit_logger = AuditLogger(
    enabled=config_manager.config.audit_logging.enabled,
    log_path=config_manager.config.audit_logging.log_path,
)

# --- MCP Server ---
mcp = FastMCP("Google Personal MCP Server")


def get_sheets_service(alias: str) -> Tuple[SheetsService, str]:
    resource = config_manager.get_sheet_resource(alias)
    context = GoogleContext(profile=resource.profile)
    return SheetsService(context), resource.id


def get_drive_service(alias: str) -> Tuple[DriveService, str]:
    resource = config_manager.get_folder_resource(alias)
    context = GoogleContext(profile=resource.profile)
    # Important: The drive service should be restricted to IDs for THIS profile
    allowed_ids = config_manager.get_allowed_folder_ids(resource.profile)
    return DriveService(context, allowed_folder_ids=allowed_ids), resource.id


# --- Configuration Tools ---


def _wrap_tool_execution(func, tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Wrap tool execution with request ID tracking and audit logging.

    Args:
        func: Function to execute
        tool_name: Name of the tool
        **kwargs: Arguments to pass to function

    Returns:
        Result dict with request_id included
    """
    request_id = set_request_id()
    try:
        result = func(**kwargs)

        # Log successful tool execution
        audit_logger.log_tool_call(
            tool_name=tool_name, parameters=kwargs, request_id=request_id, success=True
        )

        # Add request_id to response
        if isinstance(result, dict):
            result["request_id"] = request_id

        return result
    except Exception as e:
        error_msg = str(e)
        if should_sanitize():
            error_msg = mask_credentials(error_msg)

        # Log failed tool execution
        audit_logger.log_tool_call(
            tool_name=tool_name,
            parameters=kwargs,
            request_id=request_id,
            success=False,
            error_message=error_msg,
        )

        return {"status": "error", "message": error_msg, "request_id": request_id}
    finally:
        clear_request_id()


# --- Health Check Tool ---


@mcp.tool()
def health_check() -> dict:
    """
    Health check tool that verifies server readiness.

    Returns server health status with component-level diagnostics.
    """
    request_id = set_request_id()

    try:
        components = {}

        # Check config
        try:
            sheets_count = len(config_manager.list_sheets())
            folders_count = len(config_manager.list_folders())
            components["config"] = {
                "status": "ok",
                "sheets_configured": sheets_count,
                "folders_configured": folders_count,
            }
        except Exception as e:
            components["config"] = {"status": "error", "message": str(e)}

        # Check each profile
        all_profiles = set()
        for sheet_config in config_manager.config.sheets.values():
            all_profiles.add(sheet_config.profile)
        for folder_config in config_manager.config.drive_folders.values():
            all_profiles.add(folder_config.profile)

        for profile in all_profiles:
            try:
                context = GoogleContext(profile=profile)
                # Try to get credentials (this validates they work)
                _ = context.credentials
                components[f"auth_{profile}"] = {
                    "status": "ok",
                    "profile": profile,
                    "token_valid": True,
                }
            except Exception as e:
                components[f"auth_{profile}"] = {
                    "status": "error",
                    "profile": profile,
                    "message": str(e),
                }

        # Determine overall status
        errors = sum(1 for c in components.values() if c.get("status") == "error")
        if errors == 0:
            overall_status = "healthy"
        elif errors < len(components) / 2:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        result = {
            "status": overall_status,
            "version": "0.2.0",
            "components": components,
            "timestamp": datetime.now().isoformat() + "Z",
            "request_id": request_id,
        }

        # Log health check
        audit_logger.log_tool_call(
            tool_name="health_check", parameters={}, request_id=request_id, success=True
        )

        return result
    except Exception as e:
        error_msg = str(e)
        if should_sanitize():
            error_msg = mask_credentials(error_msg)

        result = {
            "status": "unhealthy",
            "message": error_msg,
            "timestamp": datetime.now().isoformat() + "Z",
            "request_id": request_id,
        }

        audit_logger.log_tool_call(
            tool_name="health_check",
            parameters={},
            request_id=request_id,
            success=False,
            error_message=error_msg,
        )

        return result
    finally:
        clear_request_id()


# --- Configuration Tools ---


@mcp.tool()
def list_configured_sheets(profile: str = "default") -> dict:
    """Lists all configured Google Sheets for a profile."""
    request_id = set_request_id()
    try:
        sheets = config_manager.list_sheets(profile)
        result = []
        for alias, config in sheets.items():
            result.append(
                {
                    "alias": alias,
                    "spreadsheet_id": config.id,
                    "description": config.description or "",
                    "profile": config.profile,
                }
            )

        audit_logger.log_tool_call(
            tool_name="list_configured_sheets",
            parameters={"profile": profile},
            request_id=request_id,
            success=True,
        )

        return {"status": "success", "sheets": result, "request_id": request_id}
    except Exception as e:
        error_msg = str(e)
        if should_sanitize():
            error_msg = mask_credentials(error_msg)

        audit_logger.log_tool_call(
            tool_name="list_configured_sheets",
            parameters={"profile": profile},
            request_id=request_id,
            success=False,
            error_message=error_msg,
        )

        return {"status": "error", "message": error_msg, "request_id": request_id}
    finally:
        clear_request_id()


@mcp.tool()
def list_configured_folders(profile: str = "default") -> dict:
    """Lists all configured Google Drive folders for a profile."""
    try:
        folders = config_manager.list_folders(profile)
        result = []
        for alias, config in folders.items():
            result.append(
                {
                    "alias": alias,
                    "folder_id": config.id,
                    "description": config.description or "",
                    "profile": config.profile,
                }
            )
        return {"status": "success", "folders": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- Sheets Tools ---


@mcp.tool()
def list_sheets(sheet_alias: str) -> list[str]:
    """Lists all sheets (tabs) in a given spreadsheet identified by its alias."""
    try:
        service, spreadsheet_id = get_sheets_service(sheet_alias)
        return service.list_sheet_titles(spreadsheet_id)
    except Exception as e:
        return [f"Error: {str(e)}"]


@mcp.tool()
def get_sheet_status(sheet_alias: str, range_name: str = "README!A1") -> dict:
    """Gets the status (values) of a sheet range."""
    try:
        service, spreadsheet_id = get_sheets_service(sheet_alias)
        values = service.read_range(spreadsheet_id, range_name)
        return {"status": "success", "data": values}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def insert_prompt(
    sheet_tab_name: str,
    prompt_name: str,
    content: str,
    sheet_alias: str,
    author: str = "Google MCP",
) -> dict:
    """Inserts a prompt into a specific sheet tab."""
    try:
        service, spreadsheet_id = get_sheets_service(sheet_alias)
        timestamp = datetime.now().isoformat()
        values = [prompt_name, content, author, timestamp, author, timestamp]
        service.insert_row_at_top(spreadsheet_id, sheet_tab_name, values)
        return {"status": "success", "message": "Prompt inserted successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_prompts(sheet_tab_name: str, sheet_alias: str) -> dict:
    """Gets all prompts from a sheet tab."""
    try:
        service, spreadsheet_id = get_sheets_service(sheet_alias)
        range_name = f"{sheet_tab_name}!A:F"
        raw_values = service.read_range(spreadsheet_id, range_name)

        if not raw_values:
            return {"status": "success", "prompts": []}

        headers = [
            "Name",
            "Content",
            "Created By",
            "Created At",
            "Last Modified By",
            "Last Modified At",
        ]
        prompts = []
        for row in raw_values[1:]:
            prompt_dict = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
            prompts.append(prompt_dict)

        return {"status": "success", "prompts": prompts}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- Drive Tools ---


@mcp.tool()
def list_drive_files(folder_alias: str) -> dict:
    """Lists files in a configured Google Drive folder."""
    try:
        service, folder_id = get_drive_service(folder_alias)
        files = service.list_files(folder_id)
        return {"status": "success", "files": files}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def upload_file(local_path: str, folder_alias: str, filename: Optional[str] = None) -> dict:
    """Uploads a local file to a configured Google Drive folder."""
    try:
        service, folder_id = get_drive_service(folder_alias)
        file = service.upload_file(local_path, folder_id, filename)
        return {"status": "success", "file_id": file.get("id"), "message": "Upload successful"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_file_content(file_id: str, folder_alias: str) -> dict:
    """Downloads a file's content from a specific folder alias."""
    try:
        service, _ = get_drive_service(folder_alias)
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            service.download_file(file_id, tmp.name)
            return {"status": "success", "local_path": tmp.name, "message": "File downloaded."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def delete_file(file_id: str, folder_alias: str) -> dict:
    """Deletes a file from Google Drive."""
    try:
        service, _ = get_drive_service(folder_alias)
        service.remove_file(file_id)
        return {"status": "success", "message": f"File {file_id} deleted."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def async_main():
    await mcp.run_stdio_async()


def main():
    import anyio

    anyio.run(async_main)


if __name__ == "__main__":
    main()
