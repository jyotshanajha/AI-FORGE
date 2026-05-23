import json
import re

import gspread
import pandas as pd
from fastapi import HTTPException
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound

from app.core.config import settings


def _extract_google_sheet_key(value: str) -> str:
    trimmed = value.strip()
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", trimmed)
    key = match.group(1) if match else trimmed

    # Google spreadsheet keys use URL-safe characters only.
    if not re.fullmatch(r"[a-zA-Z0-9-_]+", key):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_google_sheet_id",
                "message": "Invalid Google Sheet ID. Copy the full URL directly from the browser address bar.",
            },
        )
    return key


def _build_gspread_client() -> gspread.Client:
    raw_value = settings.GOOGLE_SERVICE_ACCOUNT_JSON
    if not raw_value:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "google_sheets_unavailable",
                "message": "GOOGLE_SERVICE_ACCOUNT_JSON is not configured",
            },
        )

    try:
        credentials = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "invalid_google_service_account",
                "message": "GOOGLE_SERVICE_ACCOUNT_JSON must be a full JSON string, not a file path.",
            },
        ) from exc

    # gspread >= 6.x requires service_account_from_dict for in-memory credentials.
    return gspread.service_account_from_dict(credentials)


def _normalize_worksheet_title(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def _resolve_worksheet(spreadsheet: gspread.Spreadsheet, worksheet_name: str | None) -> gspread.Worksheet:
    if not worksheet_name:
        worksheet = spreadsheet.get_worksheet(0)
        if worksheet is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "worksheet_not_found", "message": "Spreadsheet has no worksheets"},
            )
        return worksheet

    requested_name = worksheet_name.strip()
    try:
        return spreadsheet.worksheet(requested_name)
    except WorksheetNotFound:
        pass

    worksheets = spreadsheet.worksheets()
    normalized_requested = _normalize_worksheet_title(requested_name)
    for worksheet in worksheets:
        if _normalize_worksheet_title(worksheet.title) == normalized_requested:
            return worksheet

    available_names = ", ".join(worksheet.title for worksheet in worksheets) if worksheets else "(none)"
    raise HTTPException(
        status_code=404,
        detail={
            "error": "worksheet_not_found",
            "message": (
                f"Worksheet '{worksheet_name}' not found. "
                f"Available worksheets: {available_names}."
            ),
        },
    )


def load_sheet_as_dataframe(google_sheet_id_or_url: str, worksheet_name: str | None = None) -> pd.DataFrame:
    client = _build_gspread_client()
    sheet_key = _extract_google_sheet_key(google_sheet_id_or_url)

    try:
        spreadsheet = client.open_by_key(sheet_key)
        worksheet = _resolve_worksheet(spreadsheet, worksheet_name)
        values = worksheet.get_all_values()
    except HTTPException:
        raise
    except SpreadsheetNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "google_sheet_not_found",
                "message": (
                    "Google Sheet not found or not shared with the configured service account. "
                    "Verify the spreadsheet ID and sharing permissions."
                ),
            },
        ) from exc
    except APIError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "google_sheet_api_error",
                "message": f"Google Sheets API request failed: {exc}",
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "google_sheet_load_failed",
                "message": (
                    "Failed to load Google Sheet. Ensure the sheet is shared with the service account email "
                    "(Viewer or higher), the spreadsheet ID is correct, and network access to googleapis.com is allowed. "
                    f"Details: {exc}"
                ),
            },
        ) from exc

    if not values:
        return pd.DataFrame()

    headers = values[0]
    rows = values[1:] if len(values) > 1 else []
    return pd.DataFrame(rows, columns=headers).fillna("")