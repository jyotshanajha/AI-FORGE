import json
import re
import uuid
from pathlib import Path
from typing import Any

import gspread
import pandas as pd
from fastapi import HTTPException
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

from app.ai.llm import llm
from app.core.config import settings
from app.models.user import User
from app.schemas.agents import DataframeQueryRequest, DataframeQueryResponse
from app.services.attachment_service import AttachmentService


class DataframeQueryService:
    @staticmethod
    def answer_question(payload: DataframeQueryRequest, current_user: User) -> DataframeQueryResponse:
        dataframe, source_type, source_name = DataframeQueryService._load_dataframe(payload, current_user)
        agent = DataframeQueryService._build_agent(dataframe)
        prompt = DataframeQueryService._build_prompt(payload.question, dataframe)

        try:
            result = agent.invoke(
                {"input": prompt},
                config={"metadata": {"user_email": current_user.email}},
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail={"error": "dataframe_query_failed", "message": str(exc)},
            ) from exc

        answer = str(result.get("output", "")).strip()
        if not answer:
            raise HTTPException(
                status_code=502,
                detail={"error": "dataframe_query_failed", "message": "Empty dataframe agent response"},
            )

        steps, generated_code = DataframeQueryService._extract_intermediate_steps(result.get("intermediate_steps"))
        return DataframeQueryResponse(
            answer=answer,
            source_type=source_type,
            source_name=source_name,
            row_count=int(dataframe.shape[0]),
            column_count=int(dataframe.shape[1]),
            columns=[str(column) for column in list(dataframe.columns)],
            generated_code=generated_code,
            intermediate_steps=steps,
        )

    @staticmethod
    def _build_prompt(question: str, dataframe: pd.DataFrame) -> str:
        preview_rows = min(5, len(dataframe.index))
        column_list = ", ".join(str(column) for column in list(dataframe.columns)) or "No columns"
        return (
            "You are answering questions about a tabular dataset loaded into a pandas DataFrame named df. "
            "Use only the dataframe content to answer the question. "
            f"The dataframe has {len(dataframe.index)} rows and {len(dataframe.columns)} columns. "
            f"Columns: {column_list}. "
            f"Reference up to the first {preview_rows} rows when helpful. "
            f"Question: {question}"
        )

    @staticmethod
    def _build_agent(dataframe: pd.DataFrame) -> Any:
        if llm is None:
            raise HTTPException(
                status_code=503,
                detail={"error": "llm_unavailable", "message": "LLM client is not configured"},
            )

        errors: list[str] = []
        for agent_type in ("tool-calling", "openai-tools"):
            try:
                return create_pandas_dataframe_agent(
                    llm=llm,
                    df=dataframe,
                    agent_type=agent_type,
                    verbose=False,
                    allow_dangerous_code=True,
                    return_intermediate_steps=True,
                )
            except Exception as exc:
                errors.append(f"{agent_type}: {exc}")

        raise HTTPException(
            status_code=502,
            detail={"error": "agent_initialization_failed", "message": " | ".join(errors)},
        )

    @staticmethod
    def _load_dataframe(payload: DataframeQueryRequest, current_user: User) -> tuple[pd.DataFrame, str, str]:
        if payload.attachment_id is not None:
            return DataframeQueryService._load_from_attachment(current_user.id, payload.attachment_id)
        return DataframeQueryService._load_from_google_sheet(payload.google_sheet_id or "", payload.worksheet_name)

    @staticmethod
    def _load_from_attachment(user_id: uuid.UUID, attachment_id: uuid.UUID) -> tuple[pd.DataFrame, str, str]:
        resolved = AttachmentService.get_download_path(user_id, attachment_id)
        if not resolved:
            raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Attachment not found"})

        stored_path, filename, _mime_type = resolved
        lower_name = filename.lower()
        if lower_name.endswith(".csv"):
            dataframe = pd.read_csv(stored_path)
        elif lower_name.endswith((".xlsx", ".xls")):
            dataframe = pd.read_excel(stored_path)
        else:
            raise HTTPException(
                status_code=400,
                detail={"error": "unsupported_source", "message": "Only .csv, .xls, and .xlsx files are supported"},
            )

        return dataframe.fillna(""), "attachment", filename

    @staticmethod
    def _load_from_google_sheet(google_sheet_id: str, worksheet_name: str | None) -> tuple[pd.DataFrame, str, str]:
        client = DataframeQueryService._build_gspread_client()
        sheet_key = DataframeQueryService._extract_google_sheet_key(google_sheet_id)

        try:
            spreadsheet = client.open_by_key(sheet_key)
            worksheet = spreadsheet.worksheet(worksheet_name) if worksheet_name else spreadsheet.get_worksheet(0)
            if worksheet is None:
                raise HTTPException(
                    status_code=404,
                    detail={"error": "worksheet_not_found", "message": "Worksheet not found"},
                )
            values = worksheet.get_all_values()
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail={"error": "google_sheet_load_failed", "message": str(exc)},
            ) from exc

        if not values:
            return pd.DataFrame(), "google_sheet", spreadsheet.title

        headers = values[0]
        rows = values[1:] if len(values) > 1 else []
        dataframe = pd.DataFrame(rows, columns=headers)
        source_name = f"{spreadsheet.title}:{worksheet.title}"
        return dataframe.fillna(""), "google_sheet", source_name

    @staticmethod
    def _build_gspread_client() -> gspread.Client:
        raw_value = settings.GOOGLE_SERVICE_ACCOUNT_JSON
        if not raw_value:
            raise HTTPException(
                status_code=503,
                detail={"error": "google_sheets_unavailable", "message": "GOOGLE_SERVICE_ACCOUNT_JSON is not configured"},
            )

        path_candidate = Path(raw_value)
        if path_candidate.exists():
            return gspread.service_account(filename=str(path_candidate))

        try:
            credentials = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "invalid_google_service_account",
                    "message": "GOOGLE_SERVICE_ACCOUNT_JSON must be a file path or JSON payload",
                },
            ) from exc

        return gspread.service_account_from_dict(credentials)

    @staticmethod
    def _extract_google_sheet_key(value: str) -> str:
        trimmed = value.strip()
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", trimmed)
        return match.group(1) if match else trimmed

    @staticmethod
    def _extract_intermediate_steps(raw_steps: Any) -> tuple[list[str], str | None]:
        if not isinstance(raw_steps, list):
            return [], None

        rendered_steps: list[str] = []
        generated_code: str | None = None

        for item in raw_steps:
            if isinstance(item, tuple) and len(item) >= 2:
                action, observation = item[0], item[1]
                tool_name = str(getattr(action, "tool", "agent_step"))
                tool_input = getattr(action, "tool_input", None)

                if isinstance(tool_input, dict):
                    tool_input_text = json.dumps(tool_input, ensure_ascii=True)
                elif tool_input is None:
                    tool_input_text = ""
                else:
                    tool_input_text = str(tool_input)

                observation_text = str(observation)
                rendered_steps.append(f"{tool_name}: {tool_input_text} => {observation_text}".strip())

                if generated_code is None and tool_input_text:
                    generated_code = tool_input_text
                continue

            rendered_steps.append(str(item))

        return rendered_steps, generated_code