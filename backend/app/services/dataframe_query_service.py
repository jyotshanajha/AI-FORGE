import asyncio
import importlib.metadata
import json
import logging
import sys
import uuid
from typing import Any

import pandas as pd
from fastapi import HTTPException

from app.ai.llm import llm
from app.models.user import User
from app.schemas.agents import DataframeQueryRequest, DataframeQueryResponse
from app.services.attachment_service import AttachmentService
from app.services.sheets_service import load_sheet_as_dataframe


MAX_INTERMEDIATE_STEPS = 20
MAX_STEP_LENGTH = 1200
logger = logging.getLogger(__name__)


class DataframeQueryService:
    @staticmethod
    def _runtime_diagnostics() -> str:
        package_names = ("langchain", "langchain-experimental", "langchain-community", "langchain-core")
        versions: list[str] = []
        for package_name in package_names:
            try:
                versions.append(f"{package_name}={importlib.metadata.version(package_name)}")
            except importlib.metadata.PackageNotFoundError:
                versions.append(f"{package_name}=not-installed")
        python_version = sys.version.split()[0]
        return f"Python={python_version}, Executable={sys.executable}, Packages=[{', '.join(versions)}]"

    @staticmethod
    async def answer_question(payload: DataframeQueryRequest, current_user: User) -> DataframeQueryResponse:
        dataframe, source_type, source_name = DataframeQueryService._load_dataframe(payload, current_user)
        execution_result = await DataframeQueryService._run_agent(
            question=payload.question,
            dataframe=dataframe,
            user_email=current_user.email,
        )
        answer = DataframeQueryService._extract_answer(execution_result)
        steps = DataframeQueryService._normalize_intermediate_steps(execution_result.get("intermediate_steps"))
        generated_code = DataframeQueryService._extract_generated_code(steps)

        if not answer:
            raise HTTPException(
                status_code=502,
                detail={"error": "dataframe_query_failed", "message": "Empty dataframe agent response"},
            )

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
    async def _run_agent(question: str, dataframe: pd.DataFrame, user_email: str) -> dict[str, Any]:
        if sys.version_info < (3, 11):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "unsupported_python",
                    "message": (
                        "Dataframe agent requires Python 3.11+ in this project. "
                        f"{DataframeQueryService._runtime_diagnostics()}"
                    ),
                },
            )

        if llm is None:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "llm_unavailable",
                    "message": (
                        "LLM client is not configured. "
                        "Set LITELLM_PROXY_URL, LITELLM_API_KEY, and LLM_MODEL in backend environment. "
                        f"{DataframeQueryService._runtime_diagnostics()}"
                    ),
                },
            )

        try:
            from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
        except ModuleNotFoundError as exc:
            logger.exception("Dataframe agent dependency import failed: %s", exc)
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "dependency_missing",
                    "message": (
                        "langchain-experimental is required for dataframe agent execution. "
                        f"Details: {type(exc).__name__}: {exc}. {DataframeQueryService._runtime_diagnostics()}"
                    ),
                },
            ) from exc
        except Exception as exc:
            logger.exception("Dataframe agent toolkit import failed: %s", exc)
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "agent_unavailable",
                    "message": (
                        "LangChain dataframe agent could not be initialized in this Python environment. "
                        "Use Python 3.11+ for this project and ensure langchain/langchain-experimental versions are compatible. "
                        f"Details: {type(exc).__name__}: {exc}. {DataframeQueryService._runtime_diagnostics()}"
                    ),
                },
            ) from exc

        try:
            agent_executor = create_pandas_dataframe_agent(
                llm=llm,
                df=dataframe,
                agent_type="zero-shot-react-description",
                include_df_in_prompt=True,
                number_of_head_rows=min(5, len(dataframe.index)),
                max_iterations=8,
                early_stopping_method="generate",
                return_intermediate_steps=True,
                allow_dangerous_code=True,
            )
        except Exception as exc:
            logger.exception("Dataframe agent initialization failed: %s", exc)
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "agent_unavailable",
                    "message": (
                        "LangChain dataframe agent could not be initialized in this Python environment. "
                        "Use Python 3.11+ for this project and ensure langchain/langchain-experimental versions are compatible. "
                        f"Details: {type(exc).__name__}: {exc}. {DataframeQueryService._runtime_diagnostics()}"
                    ),
                },
            ) from exc

        try:
            result = await asyncio.to_thread(
                lambda: agent_executor.invoke(
                    {"input": question},
                    config={"metadata": {"user_email": user_email}},
                )
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail={"error": "dataframe_query_failed", "message": str(exc)},
            ) from exc

        if not isinstance(result, dict):
            raise HTTPException(
                status_code=502,
                detail={"error": "dataframe_query_failed", "message": "Unexpected dataframe agent response format"},
            )
        return result

    @staticmethod
    def _extract_answer(result: dict[str, Any]) -> str:
        content = result.get("output")
        return str(content).strip() if content is not None else ""

    @staticmethod
    def _normalize_intermediate_steps(raw_steps: Any) -> list[str]:
        if not isinstance(raw_steps, list):
            return []

        normalized: list[str] = []
        for item in raw_steps[:MAX_INTERMEDIATE_STEPS]:
            if isinstance(item, tuple) and len(item) == 2:
                action, observation = item
                tool_name = getattr(action, "tool", "unknown_tool")
                tool_input = getattr(action, "tool_input", "")
                action_log = getattr(action, "log", "")

                normalized.append(f"tool: {DataframeQueryService._truncate(str(tool_name), 200)}")
                if tool_input:
                    normalized.append(f"tool_input: {DataframeQueryService._truncate(str(tool_input), MAX_STEP_LENGTH)}")
                if action_log:
                    normalized.append(f"agent_log: {DataframeQueryService._truncate(str(action_log), MAX_STEP_LENGTH)}")
                normalized.append(f"observation: {DataframeQueryService._truncate(str(observation), MAX_STEP_LENGTH)}")
            else:
                normalized.append(DataframeQueryService._truncate(str(item), MAX_STEP_LENGTH))
        return normalized

    @staticmethod
    def _extract_generated_code(steps: list[str]) -> str | None:
        for step in steps:
            if step.startswith("tool_input: "):
                return step.replace("tool_input: ", "", 1).strip()
        return None

    @staticmethod
    def _truncate(value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value
        return f"{value[:max_length]}..."

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
        dataframe = load_sheet_as_dataframe(google_sheet_id, worksheet_name)
        return dataframe, "google_sheet", google_sheet_id
