import ast
import asyncio
import json
import re
import uuid
from pathlib import Path
from typing import Any

import gspread
import pandas as pd
from fastapi import HTTPException

from app.ai.llm import llm
from app.core.config import settings
from app.models.user import User
from app.schemas.agents import DataframeQueryRequest, DataframeQueryResponse
from app.services.attachment_service import AttachmentService


DATAFRAME_AGENT_PROMPT = """You are a dataframe query agent.
You must produce JSON only with this exact shape:
{
  \"pandas_expression\": \"<single Python expression>\",
  \"explanation\": \"<short explanation>\"
}

Rules:
- The expression must be a single Python expression, not statements.
- Use only the variables df and pd.
- Never use imports, file access, network calls, subprocesses, or OS access.
- Never use eval, exec, open, compile, globals, locals, vars, __import__, or dunder attributes.
- Prefer concise pandas expressions that directly answer the question.
- If the question asks for metadata like row count or columns, use pandas expressions for that.
- Return valid JSON only. No markdown fences.
"""

ANSWER_SYNTHESIS_PROMPT = """You are summarizing the result of a dataframe query for an end user.
Use only the executed dataframe result and metadata provided.
Be concise, accurate, and explicit when the result is empty.
"""

BLOCKED_NAMES = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "globals",
    "input",
    "locals",
    "open",
    "os",
    "pathlib",
    "requests",
    "shutil",
    "socket",
    "subprocess",
    "sys",
    "vars",
}

BLOCKED_TOKENS = ("__", "import ", "open(", "exec(", "eval(", "subprocess", "socket", "requests", "http")


class DataframeQueryService:
    @staticmethod
    async def answer_question(payload: DataframeQueryRequest, current_user: User) -> DataframeQueryResponse:
        dataframe, source_type, source_name = DataframeQueryService._load_dataframe(payload, current_user)
        generated_code, explanation = await DataframeQueryService._plan_query(payload.question, dataframe, current_user.email)
        result = await asyncio.to_thread(DataframeQueryService._evaluate_expression, generated_code, dataframe)
        result_preview = DataframeQueryService._format_result_preview(result)
        answer = await DataframeQueryService._synthesize_answer(
            question=payload.question,
            dataframe=dataframe,
            result_preview=result_preview,
            explanation=explanation,
            user_email=current_user.email,
        )

        if not answer:
            raise HTTPException(
                status_code=502,
                detail={"error": "dataframe_query_failed", "message": "Empty dataframe agent response"},
            )

        steps = [
            f"planned_expression: {generated_code}",
            f"planner_explanation: {explanation}",
            f"result_preview: {result_preview}",
        ]
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
    def _build_planning_prompt(question: str, dataframe: pd.DataFrame) -> str:
        preview_rows = min(5, len(dataframe.index))
        preview_text = dataframe.head(preview_rows).to_csv(index=False) if preview_rows > 0 else "<empty dataframe>"
        dtypes_text = ", ".join(f"{column}: {dtype}" for column, dtype in dataframe.dtypes.items()) or "No columns"
        return (
            f"{DATAFRAME_AGENT_PROMPT}\n\n"
            f"Dataframe shape: rows={len(dataframe.index)}, columns={len(dataframe.columns)}\n"
            f"Columns and dtypes: {dtypes_text}\n"
            f"Preview rows (CSV):\n{preview_text}\n"
            f"Question: {question}\n"
        )

    @staticmethod
    async def _plan_query(question: str, dataframe: pd.DataFrame, user_email: str) -> tuple[str, str]:
        if llm is None:
            raise HTTPException(
                status_code=503,
                detail={"error": "llm_unavailable", "message": "LLM client is not configured"},
            )

        prompt = DataframeQueryService._build_planning_prompt(question, dataframe)
        response = await llm.ainvoke(prompt, config={"metadata": {"user_email": user_email}})
        content = response.content if hasattr(response, "content") else str(response)
        plan = DataframeQueryService._parse_json_payload(str(content))

        expression = str(plan.get("pandas_expression", "")).strip()
        explanation = str(plan.get("explanation", "")).strip() or "No explanation provided"
        DataframeQueryService._validate_expression(expression)
        return expression, explanation

    @staticmethod
    def _parse_json_payload(content: str) -> dict[str, Any]:
        candidate = content.strip()
        candidate = re.sub(r"^```(?:json)?", "", candidate, flags=re.IGNORECASE).strip()
        candidate = re.sub(r"```$", "", candidate).strip()

        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
            if not match:
                raise HTTPException(
                    status_code=502,
                    detail={"error": "dataframe_query_failed", "message": "Planner did not return valid JSON"},
                )
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=502,
                    detail={"error": "dataframe_query_failed", "message": "Planner returned malformed JSON"},
                ) from exc

        if not isinstance(parsed, dict):
            raise HTTPException(
                status_code=502,
                detail={"error": "dataframe_query_failed", "message": "Planner JSON must be an object"},
            )
        return parsed

    @staticmethod
    def _validate_expression(expression: str) -> None:
        cleaned = expression.strip()
        if not cleaned:
            raise HTTPException(
                status_code=502,
                detail={"error": "dataframe_query_failed", "message": "Planner returned an empty expression"},
            )

        lowered = cleaned.lower()
        for token in BLOCKED_TOKENS:
            if token in lowered:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "unsafe_expression", "message": f"Blocked unsafe token in expression: {token}"},
                )

        try:
            tree = ast.parse(cleaned, mode="eval")
        except SyntaxError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_expression", "message": str(exc)},
            ) from exc

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in BLOCKED_NAMES:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "unsafe_expression", "message": f"Blocked unsafe name in expression: {node.id}"},
                )
            if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
                raise HTTPException(
                    status_code=400,
                    detail={"error": "unsafe_expression", "message": "Dunder attributes are not allowed"},
                )

    @staticmethod
    def _evaluate_expression(expression: str, dataframe: pd.DataFrame) -> Any:
        try:
            return eval(expression, {"__builtins__": {}}, {"df": dataframe, "pd": pd})
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "expression_execution_failed", "message": str(exc)},
            ) from exc

    @staticmethod
    def _format_result_preview(result: Any) -> str:
        if isinstance(result, pd.DataFrame):
            if result.empty:
                return "Empty DataFrame"
            return result.head(20).to_csv(index=False).strip()
        if isinstance(result, pd.Series):
            if result.empty:
                return "Empty Series"
            return result.head(20).to_string()
        if isinstance(result, (list, tuple, dict)):
            return json.dumps(result, default=str, ensure_ascii=True)[:4000]
        return str(result)

    @staticmethod
    async def _synthesize_answer(
        question: str,
        dataframe: pd.DataFrame,
        result_preview: str,
        explanation: str,
        user_email: str,
    ) -> str:
        if llm is None:
            raise HTTPException(
                status_code=503,
                detail={"error": "llm_unavailable", "message": "LLM client is not configured"},
            )

        prompt = (
            f"{ANSWER_SYNTHESIS_PROMPT}\n\n"
            f"Question: {question}\n"
            f"Dataframe shape: rows={len(dataframe.index)}, columns={len(dataframe.columns)}\n"
            f"Planner explanation: {explanation}\n"
            f"Executed result:\n{result_preview}\n"
        )
        response = await llm.ainvoke(prompt, config={"metadata": {"user_email": user_email}})
        content = response.content if hasattr(response, "content") else str(response)
        return str(content).strip()

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
