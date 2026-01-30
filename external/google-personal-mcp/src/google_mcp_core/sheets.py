from typing import List, Dict, Any
from .context import GoogleContext


class SheetsService:
    def __init__(self, context: GoogleContext):
        self.context = context
        self.service = context.sheets

    def read_range(self, spreadsheet_id: str, range_name: str) -> List[List[Any]]:
        if not spreadsheet_id:
            raise ValueError("Spreadsheet ID is required.")
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        return result.get("values", [])

    def write_range(
        self, spreadsheet_id: str, range_name: str, values: List[List[Any]]
    ) -> Dict[str, Any]:
        body = {"values": values}
        result = (
            self.service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        return result

    def get_spreadsheet_metadata(self, spreadsheet_id: str) -> Dict[str, Any]:
        return self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

    def list_sheet_titles(self, spreadsheet_id: str) -> List[str]:
        metadata = self.get_spreadsheet_metadata(spreadsheet_id)
        return [sheet.get("properties", {}).get("title") for sheet in metadata.get("sheets", [])]

    def create_sheet(self, spreadsheet_id: str, title: str) -> Dict[str, Any]:
        requests = [{"addSheet": {"properties": {"title": title}}}]
        body = {"requests": requests}
        return (
            self.service.spreadsheets()
            .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
            .execute()
        )

    def insert_row_at_top(self, spreadsheet_id: str, sheet_name: str, values: List[Any]):
        # Get sheet properties to find sheetId
        metadata = self.get_spreadsheet_metadata(spreadsheet_id)
        sheet_id = None
        for sheet in metadata.get("sheets", []):
            if sheet.get("properties", {}).get("title") == sheet_name:
                sheet_id = sheet.get("properties", {}).get("sheetId")
                break

        if sheet_id is None:
            raise ValueError(f"Sheet '{sheet_name}' not found.")

        requests = [
            {
                "insertRange": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": 2,
                    },
                    "shiftDimension": "ROWS",
                }
            }
        ]

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": requests}
        ).execute()

        range_to_update = f"{sheet_name}!A2"
        self.write_range(spreadsheet_id, range_to_update, [values])
