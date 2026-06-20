"""
google_services.py
------------------
Thin, well-documented wrappers around the Google Drive and Google Sheets REST
APIs (via `google-api-python-client`). Every function takes a `Credentials`
object so the same code works for any signed-in user.

A custom `GoogleServiceError` is raised on failure so the UI layer can show a
friendly message instead of a raw stack trace.
"""

from __future__ import annotations

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import DRIVE_API, GOOGLE_SHEET_MIME, ORDER_COLUMNS, SHEETS_API


class GoogleServiceError(Exception):
    """Raised when a Drive/Sheets call fails for a reason worth surfacing."""


def _drive(creds):
    return build(*DRIVE_API, credentials=creds, cache_discovery=False)


def _sheets(creds):
    return build(*SHEETS_API, credentials=creds, cache_discovery=False)


# ---------------------------------------------------------------------------
# Drive: discover the user's spreadsheets
# ---------------------------------------------------------------------------
def list_spreadsheets(creds, page_size: int = 100) -> list[dict]:
    """Return [{'id', 'name'}, ...] of the user's Google Sheets.

    We filter by mimeType so only native Google Sheets show up (not Excel
    uploads or other Drive files), and exclude trashed files.
    """
    try:
        query = f"mimeType='{GOOGLE_SHEET_MIME}' and trashed=false"
        response = (
            _drive(creds)
            .files()
            .list(
                q=query,
                pageSize=page_size,
                orderBy="modifiedTime desc",
                fields="files(id, name)",
                # Include files shared with the user as well as those they own.
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        return response.get("files", [])
    except HttpError as exc:
        raise GoogleServiceError(f"Tidak bisa memuat daftar spreadsheet: {exc}") from exc


# ---------------------------------------------------------------------------
# Sheets: create a new spreadsheet with our header row
# ---------------------------------------------------------------------------
def create_spreadsheet(creds, title: str) -> dict:
    """Create a new spreadsheet and write the canonical header row.

    Returns {'id', 'name'} so the caller can immediately select it.
    """
    try:
        service = _sheets(creds)
        spreadsheet = (
            service.spreadsheets()
            .create(
                body={"properties": {"title": title}},
                fields="spreadsheetId",
            )
            .execute()
        )
        sheet_id = spreadsheet["spreadsheetId"]

        # Seed row 1 with column headers so appends line up correctly.
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range="A1",
            valueInputOption="RAW",
            body={"values": [ORDER_COLUMNS]},
        ).execute()

        return {"id": sheet_id, "name": title}
    except HttpError as exc:
        raise GoogleServiceError(f"Gagal membuat spreadsheet baru: {exc}") from exc


def _ensure_header(service, spreadsheet_id: str) -> None:
    """Write the header row if the sheet is currently empty.

    Protects against appending data into a blank sheet (e.g. one the user
    created manually) where the columns would otherwise have no labels.
    """
    existing = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range="A1:Z1")
        .execute()
        .get("values", [])
    )
    if not existing:
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="A1",
            valueInputOption="RAW",
            body={"values": [ORDER_COLUMNS]},
        ).execute()


# ---------------------------------------------------------------------------
# Sheets: append parsed order rows
# ---------------------------------------------------------------------------
def append_rows(creds, spreadsheet_id: str, df: pd.DataFrame) -> int:
    """Append a DataFrame of orders to the spreadsheet. Returns rows written.

    Key Sheets API details:
      * We reindex the DataFrame to ORDER_COLUMNS so the column order in the
        sheet is deterministic regardless of how the user reordered the editor.
      * `valueInputOption="USER_ENTERED"` lets Sheets interpret numbers/dates
        naturally (so 15000 becomes a number, not the text "15000").
      * `insertDataOption="INSERT_ROWS"` always adds new rows at the bottom
        rather than overwriting a partially-filled trailing row.
    """
    if df is None or df.empty:
        return 0

    try:
        service = _sheets(creds)
        _ensure_header(service, spreadsheet_id)

        # Guarantee column order + replace pandas/NumPy NaN with empty strings,
        # which the Sheets API serialises cleanly.
        ordered = df.reindex(columns=ORDER_COLUMNS)
        values = ordered.where(ordered.notna(), "").astype(object).values.tolist()

        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range="A1",  # Sheets auto-detects the table that starts here.
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": values},
            )
            .execute()
        )
        return result.get("updates", {}).get("updatedRows", len(values))
    except HttpError as exc:
        raise GoogleServiceError(f"Gagal menyimpan ke Google Sheets: {exc}") from exc


# ---------------------------------------------------------------------------
# Sheets: read the whole sheet back as a DataFrame
# ---------------------------------------------------------------------------
def read_sheet(creds, spreadsheet_id: str, sheet_range: str = "A1:Z100000") -> pd.DataFrame:
    """Read a sheet into a DataFrame, using row 1 as the column headers."""
    try:
        result = (
            _sheets(creds)
            .spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=sheet_range)
            .execute()
        )
        rows = result.get("values", [])
        if not rows:
            return pd.DataFrame(columns=ORDER_COLUMNS)

        header, *data = rows
        # Rows from Sheets can be "ragged" (trailing empty cells omitted), so we
        # pad every row to the header width before constructing the DataFrame.
        width = len(header)
        padded = [row + [""] * (width - len(row)) for row in data]
        return pd.DataFrame(padded, columns=header)
    except HttpError as exc:
        raise GoogleServiceError(f"Gagal membaca data dari Google Sheets: {exc}") from exc
