import mimetypes
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.services.fallback_store import get_store, update_store


class AttachmentService:
    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _upload_root() -> Path:
        root = Path(settings.UPLOAD_DIR).resolve()
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _classify_attachment(mime_type: str, filename: str) -> str:
        lower_mime = mime_type.lower()
        lower_name = filename.lower()

        if lower_mime.startswith("image/"):
            return "image"
        if lower_mime.startswith("video/"):
            return "video"
        if "pdf" in lower_mime or lower_name.endswith(".pdf"):
            return "document"
        if "csv" in lower_mime or "spreadsheet" in lower_mime or lower_name.endswith((".csv", ".xls", ".xlsx")):
            return "table"
        if "javascript" in lower_mime or "python" in lower_mime or lower_name.endswith((".py", ".js", ".ts", ".tsx", ".java", ".cpp", ".cs", ".go", ".rs")):
            return "code"
        if lower_mime in {"application/x-tex", "text/x-tex"} or "latex" in lower_mime or lower_name.endswith((".tex", ".latex")):
            return "formula"
        return "file"

    @staticmethod
    async def upload_attachment(user_id: uuid.UUID, file: UploadFile) -> dict[str, object]:
        if not file.filename:
            raise HTTPException(status_code=400, detail={"error": "invalid_file", "message": "Missing file name"})

        mime_type = (file.content_type or "application/octet-stream").lower()
        if mime_type == "application/octet-stream":
            guessed_mime = mimetypes.guess_type(file.filename)[0]
            if guessed_mime:
                mime_type = guessed_mime.lower()

        if mime_type not in settings.allowed_attachment_mime_types:
            raise HTTPException(
                status_code=415,
                detail={
                    "error": "unsupported_media_type",
                    "message": f"File type '{mime_type}' is not allowed",
                },
            )

        content = await file.read()
        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail={"error": "file_too_large", "message": f"File exceeds {settings.MAX_UPLOAD_MB}MB limit"},
            )

        attachment_id = uuid.uuid4()
        safe_name = Path(file.filename).name
        user_dir = AttachmentService._upload_root() / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{attachment_id}_{safe_name}"
        stored_path = user_dir / stored_name
        stored_path.write_bytes(content)

        metadata = {
            "id": str(attachment_id),
            "user_id": str(user_id),
            "message_id": None,
            "filename": safe_name,
            "mime_type": mime_type,
            "size_bytes": len(content),
            "attachment_type": AttachmentService._classify_attachment(mime_type, safe_name),
            "stored_path": str(stored_path),
            "created_at": AttachmentService._now_utc().isoformat(),
        }

        def _mutator(store: dict) -> None:
            pending_by_user = store.setdefault("pending_attachments_by_user_id", {})
            pending = pending_by_user.setdefault(str(user_id), {})
            pending[str(attachment_id)] = metadata

            by_id = store.setdefault("attachments_by_id", {})
            by_id[str(attachment_id)] = metadata

        update_store(_mutator)
        return AttachmentService._to_response(metadata)

    @staticmethod
    def bind_attachments_to_message(
        user_id: uuid.UUID,
        attachment_ids: list[uuid.UUID],
        message_id: uuid.UUID,
    ) -> list[dict[str, object]]:
        if not attachment_ids:
            return []

        selected: list[dict[str, object]] = []

        def _mutator(store: dict) -> None:
            pending_by_user = store.setdefault("pending_attachments_by_user_id", {})
            pending = pending_by_user.setdefault(str(user_id), {})
            by_id = store.setdefault("attachments_by_id", {})
            by_message = store.setdefault("attachments_by_message_id", {})

            message_key = str(message_id)
            bucket = by_message.setdefault(message_key, [])

            for attachment_id in attachment_ids:
                key = str(attachment_id)
                metadata = pending.pop(key, None)
                if not metadata:
                    continue
                if metadata.get("user_id") != str(user_id):
                    continue

                metadata["message_id"] = message_key
                bucket.append(metadata)
                by_id[key] = metadata
                selected.append(metadata)

        update_store(_mutator)
        return [AttachmentService._to_response(item) for item in selected]

    @staticmethod
    def get_attachments_for_message_ids(user_id: uuid.UUID, message_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[dict[str, object]]]:
        store = get_store()
        by_message = store.get("attachments_by_message_id", {})
        if not isinstance(by_message, dict):
            return {}

        result: dict[uuid.UUID, list[dict[str, object]]] = {}
        for message_id in message_ids:
            rows = by_message.get(str(message_id), [])
            if not isinstance(rows, list):
                continue
            filtered: list[dict[str, object]] = []
            for item in rows:
                if not isinstance(item, dict):
                    continue
                if item.get("user_id") != str(user_id):
                    continue
                filtered.append(AttachmentService._to_response(item))
            if filtered:
                result[message_id] = filtered
        return result

    @staticmethod
    def get_download_path(user_id: uuid.UUID, attachment_id: uuid.UUID) -> tuple[Path, str, str] | None:
        store = get_store()
        by_id = store.get("attachments_by_id", {})
        if not isinstance(by_id, dict):
            return None

        metadata = by_id.get(str(attachment_id))
        if not isinstance(metadata, dict):
            return None
        if metadata.get("user_id") != str(user_id):
            return None

        stored_path = Path(str(metadata.get("stored_path", "")))
        if not stored_path.exists():
            return None

        filename = str(metadata.get("filename", "attachment"))
        mime_type = str(metadata.get("mime_type", "application/octet-stream"))
        return stored_path, filename, mime_type

    @staticmethod
    def _to_response(metadata: dict[str, object]) -> dict[str, object]:
        return {
            "id": uuid.UUID(str(metadata["id"])),
            "filename": str(metadata["filename"]),
            "mime_type": str(metadata["mime_type"]),
            "size_bytes": int(metadata["size_bytes"]),
            "attachment_type": str(metadata["attachment_type"]),
            "download_url": f"/chat/attachments/{metadata['id']}/download",
        }

    @staticmethod
    async def ingest_pdf_if_needed(
        user_id: uuid.UUID,
        user_email: str,
        attachment_id: uuid.UUID,
        mime_type: str,
        filename: str,
        stored_path: str,
    ) -> None:
        """
        Ingest PDF into ChromaDB if it's a PDF attachment.
        This runs asynchronously to not block attachment upload.
        """
        if mime_type.lower() not in {"application/pdf", "application/x-pdf"}:
            return

        try:
            from app.services.rag_service import get_rag_service
            rag = get_rag_service()
            await rag.ingest_pdf(
                pdf_path=stored_path,
                user_id=str(user_id),
                user_email=user_email,
                filename=filename,
            )
        except Exception as e:
            # Log but don't fail attachment upload if RAG ingestion fails
            print(f"Warning: PDF ingestion failed for {filename}: {str(e)}")
