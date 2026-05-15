import asyncio
import json
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.session import SessionLocal
from app.models.user import User
from app.models.upload_metadata import UploadMetadata
from app.services.fallback_store import get_store


def _parse_dt(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _collect_source_rows() -> list[dict[str, object]]:
    store = get_store()
    by_id = store.get("attachments_by_id", {})
    pending_by_user = store.get("pending_attachments_by_user_id", {})

    merged: dict[str, dict[str, object]] = {}

    if isinstance(by_id, dict):
        for attachment_id, metadata in by_id.items():
            if isinstance(metadata, dict):
                merged[str(attachment_id)] = metadata

    if isinstance(pending_by_user, dict):
        for user_entries in pending_by_user.values():
            if not isinstance(user_entries, dict):
                continue
            for attachment_id, metadata in user_entries.items():
                if isinstance(metadata, dict):
                    merged[str(attachment_id)] = metadata

    rows: list[dict[str, object]] = []
    for metadata in merged.values():
        attachment_id = metadata.get("id")
        user_id = metadata.get("user_id")
        filename = metadata.get("filename")
        mime_type = metadata.get("mime_type")
        size_bytes = metadata.get("size_bytes")
        stored_path = metadata.get("stored_path")
        attachment_type = metadata.get("attachment_type")

        if not all([attachment_id, user_id, filename, mime_type, stored_path, attachment_type]):
            continue

        extras = {
            "message_id": metadata.get("message_id"),
            "rag_info": metadata.get("rag_info"),
        }

        rows.append(
            {
                "id": uuid.UUID(str(attachment_id)),
                "user_id": uuid.UUID(str(user_id)),
                "filename": str(filename),
                "mime_type": str(mime_type),
                "size_bytes": int(size_bytes) if size_bytes is not None else 0,
                "file_path": str(stored_path),
                "attachment_type": str(attachment_type),
                "storage_location": "local",
                "metadata_json": json.dumps(extras, ensure_ascii=True),
                "created_at": _parse_dt(metadata.get("created_at")),
            }
        )

    return rows


async def main() -> None:
    if SessionLocal is None:
        raise RuntimeError("Database session is unavailable. Check DATABASE_URL and connectivity.")

    rows = _collect_source_rows()
    if not rows:
        print("No attachment metadata found to backfill.")
        return

    async with SessionLocal() as session:
        source_user_ids = {uuid.UUID(str(row["user_id"])) for row in rows}

        existing_user_ids = set(
            await session.scalars(select(User.id).where(User.id.in_(source_user_ids)))
        )
        missing_user_ids = source_user_ids - existing_user_ids

        if missing_user_ids:
            legacy_users = []
            for user_id in missing_user_ids:
                legacy_users.append(
                    {
                        "id": user_id,
                        "email": f"legacy-{user_id}@local.invalid",
                        "hashed_password": None,
                        "google_id": None,
                    }
                )

            user_stmt = insert(User).values(legacy_users)
            user_stmt = user_stmt.on_conflict_do_nothing(index_elements=[User.id])
            await session.execute(user_stmt)

        stmt = insert(UploadMetadata).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=[UploadMetadata.id])
        result = await session.execute(stmt)
        await session.commit()

    inserted = int(result.rowcount or 0)
    skipped = len(rows) - inserted
    print(f"Backfill completed. Source rows: {len(rows)}, inserted: {inserted}, skipped(existing): {skipped}")


if __name__ == "__main__":
    asyncio.run(main())
