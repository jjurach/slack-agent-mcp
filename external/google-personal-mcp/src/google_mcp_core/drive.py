import os
import io
import logging
from typing import List, Dict, Any, Optional
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from .context import GoogleContext

logger = logging.getLogger(__name__)


class DriveService:
    def __init__(self, context: GoogleContext, allowed_folder_ids: Optional[List[str]] = None):
        self.context = context
        self.service = context.drive
        self.allowed_folder_ids = allowed_folder_ids or []

    def _verify_access(self, file_id: str = None, parent_id: str = None):
        """Verifies if the operation is within allowed folders."""
        if not self.allowed_folder_ids:
            raise PermissionError("Drive access is disabled: No allowed folders configured.")

        # If we have a parent_id, check if it's allowed
        if parent_id:
            if parent_id not in self.allowed_folder_ids:
                raise PermissionError(f"Access to folder {parent_id} is not allowed.")

        # If we only have a file_id, we should check its parents
        if file_id:
            try:
                file = self.service.files().get(fileId=file_id, fields="parents").execute()
                parents = file.get("parents", [])
                if not any(p in self.allowed_folder_ids for p in parents):
                    raise PermissionError(
                        f"Access to file {file_id} is not allowed (not in allowed folders)."
                    )
            except Exception as e:
                # If we can't get parents (e.g. 404), we can't verify, so deny.
                raise PermissionError(f"Could not verify access for file {file_id}: {e}")

    def list_files(self, folder_id: str) -> List[Dict[str, Any]]:
        self._verify_access(parent_id=folder_id)
        query = f"'{folder_id}' in parents and trashed = false"
        results = (
            self.service.files()
            .list(q=query, fields="files(id, name, mimeType, size, modifiedTime)")
            .execute()
        )
        return results.get("files", [])

    def list_all_files(self, pageSize: int = 100) -> List[Dict[str, Any]]:
        """Lists all files accessible by the current credentials. (Admin/Script use)."""
        results = (
            self.service.files()
            .list(pageSize=pageSize, fields="nextPageToken, files(id, name, mimeType)")
            .execute()
        )
        return results.get("files", [])

    def download_file(self, file_id: str, local_path: str):
        self._verify_access(file_id=file_id)
        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(local_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            logger.debug(f"Download {int(status.progress() * 100)}%.")
        fh.close()

    def upload_file(
        self, local_path: str, folder_id: str, filename: Optional[str] = None
    ) -> Dict[str, Any]:
        self._verify_access(parent_id=folder_id)
        filename = filename or os.path.basename(local_path)
        file_metadata = {"name": filename, "parents": [folder_id]}
        media = MediaFileUpload(local_path, resumable=True)
        file = (
            self.service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        )
        return file

    def remove_file(self, file_id: str):
        self._verify_access(file_id=file_id)
        self.service.files().delete(fileId=file_id).execute()

    def find_file_by_name(self, folder_id: str, filename: str) -> Optional[str]:
        """Find a file by name in a specific folder and return its file ID.

        Args:
            folder_id: The folder to search in
            filename: The exact filename to find

        Returns:
            File ID if found, None otherwise

        Raises:
            ValueError: If multiple files with same name exist
        """
        self._verify_access(parent_id=folder_id)
        query = f"'{folder_id}' in parents and name='{filename}' and trashed = false"
        results = (
            self.service.files()
            .list(q=query, fields="files(id, name)")
            .execute()
        )
        files = results.get("files", [])

        if len(files) == 0:
            return None
        elif len(files) == 1:
            return files[0]["id"]
        else:
            raise ValueError(f"Multiple files named '{filename}' found in folder.")

    def download_file_by_name(self, folder_id: str, remote_filename: str, local_path: str):
        """Download a file by name from a folder.

        Args:
            folder_id: The folder containing the file
            remote_filename: Name of the file to download
            local_path: Local path to save the file

        Raises:
            FileNotFoundError: If remote file not found
            FileExistsError: If local file already exists
            ValueError: If multiple files with same name
        """
        if os.path.exists(local_path):
            raise FileExistsError(f"Local file already exists: {local_path}")

        file_id = self.find_file_by_name(folder_id, remote_filename)
        if not file_id:
            raise FileNotFoundError(f"File '{remote_filename}' not found in folder.")

        self.download_file(file_id, local_path)

    def remove_file_by_name(self, folder_id: str, filename: str):
        """Remove a file by name from a folder.

        Args:
            folder_id: The folder containing the file
            filename: Name of the file to remove

        Raises:
            FileNotFoundError: If file not found
            ValueError: If multiple files with same name
        """
        file_id = self.find_file_by_name(folder_id, filename)
        if not file_id:
            raise FileNotFoundError(f"File '{filename}' not found in folder.")

        self.remove_file(file_id)
