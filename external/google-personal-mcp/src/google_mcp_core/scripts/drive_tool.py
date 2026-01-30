import logging
from typing import List, Tuple
from cyclopts import App
from google_mcp_core.context import GoogleContext
from google_mcp_core.drive import DriveService

# Setup basic logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = App()


def resolve_folder_name_to_id(service, folder_name: str) -> str:
    """Finds a folder's ID by its name."""
    try:
        service.files().get(fileId=folder_name, fields="id").execute()
        return folder_name
    except Exception:
        pass

    query = f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if not files:
        raise ValueError(f"Folder '{folder_name}' not found.")
    return files[0]["id"]


def parse_mount(mount_str: str) -> Tuple[str, str, str]:
    """Parses 'profile:alias=name' or 'alias=name' or 'name'."""
    profile = "default"
    if ":" in mount_str:
        profile, rest = mount_str.split(":", 1)
    else:
        rest = mount_str

    if "=" in rest:
        alias, target = rest.split("=", 1)
    else:
        alias = target = rest

    return profile.strip(), alias.strip(), target.strip()


@app.command
def list(folder_alias: str, folder: List[str] = None):
    """List files in a mapped Google Drive folder.

    Usage: google-drive list my_alias --folder "personal:my_alias=Real Folder Name"
    """
    # Build Registry from folders
    registry = {}
    for f in folder or []:
        prof, alias, target = parse_mount(f)
        registry[alias] = (prof, target)

    if folder_alias not in registry:
        print(f"Error: Alias '{folder_alias}' not found in --folder mounts.")
        return

    profile, target_name = registry[folder_alias]
    context = GoogleContext(profile=profile)
    raw_drive = context.drive

    folder_id = resolve_folder_name_to_id(raw_drive, target_name)
    service = DriveService(context, allowed_folder_ids=[folder_id])

    files = service.list_files(folder_id)
    print(f"Files in '{folder_alias}' ({folder_id}) [Profile: {profile}]:")
    for f in files:
        print(f"{f['id']}\t{f['name']}")


# Note: get, put, remove would follow similar logic of rebuilding the transient registry.
# In a real app, this registry might be loaded from the config file automatically.

if __name__ == "__main__":
    app()
