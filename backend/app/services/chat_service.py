import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains.chat_chain import stream_chat_response
from app.models.message import Message
from app.models.thread import Thread
from app.models.user import User
from app.services.fallback_store import get_store, update_store
from app.services.thread_service import ThreadService


class ChatService:
    _in_memory_messages_by_thread: dict[uuid.UUID, list[Message]] = {}

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _load_messages_from_store() -> None:
        if ChatService._in_memory_messages_by_thread:
            return

        store = get_store()
        raw_messages = store.get("messages_by_thread_id", {})
        if not isinstance(raw_messages, dict):
            return

        loaded: dict[uuid.UUID, list[Message]] = {}
        for thread_id_str, rows in raw_messages.items():
            if not isinstance(thread_id_str, str) or not isinstance(rows, list):
                continue
            try:
                thread_id = uuid.UUID(thread_id_str)
            except ValueError:
                continue

            thread_messages: list[Message] = []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                try:
                    thread_messages.append(
                        Message(
                            id=uuid.UUID(row["id"]),
                            thread_id=thread_id,
                            role=row["role"],
                            content=row["content"],
                            created_at=datetime.fromisoformat(row["created_at"]),
                        )
                    )
                except Exception:
                    continue

            loaded[thread_id] = thread_messages

        ChatService._in_memory_messages_by_thread = loaded

    @staticmethod
    def _persist_messages_to_store() -> None:
        serializable: dict[str, list[dict[str, str]]] = {}
        for thread_id, messages in ChatService._in_memory_messages_by_thread.items():
            serializable[str(thread_id)] = [
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": (msg.created_at or ChatService._now_utc()).isoformat(),
                }
                for msg in messages
            ]

        def _mutator(store: dict) -> None:
            store["messages_by_thread_id"] = serializable

        update_store(_mutator)

    @staticmethod
    async def list_messages(db: AsyncSession, user: User, thread_id: uuid.UUID) -> list[Message]:
        await ThreadService.get_thread_or_404(db, user, thread_id)
        try:
            result = await db.execute(select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at.asc()))
            return list(result.scalars().all())
        except Exception:
            ChatService._load_messages_from_store()
            return ChatService._in_memory_messages_by_thread.get(thread_id, [])

    @staticmethod
    async def stream_reply(
        db: AsyncSession,
        user: User,
        thread_id: uuid.UUID,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        thread = await ThreadService.get_thread_or_404(db, user, thread_id)

        user_record = Message(
            id=uuid.uuid4(),
            thread_id=thread.id,
            role="user",
            content=user_message,
            created_at=ChatService._now_utc(),
        )

        use_memory_fallback = False
        try:
            db.add(user_record)
            await db.commit()
            result = await db.execute(select(Message).where(Message.thread_id == thread.id).order_by(Message.created_at.asc()))
            history_records = list(result.scalars().all())
        except Exception:
            use_memory_fallback = True
            ChatService._load_messages_from_store()
            thread_messages = ChatService._in_memory_messages_by_thread.setdefault(thread.id, [])
            thread_messages.append(user_record)
            ChatService._persist_messages_to_store()
            history_records = thread_messages

        history = [{"role": m.role, "content": m.content} for m in history_records[:-1]]

        chunks: list[str] = []
        async for chunk in stream_chat_response(user_message, history, user.email):
            chunks.append(chunk)
            yield chunk

        assistant_text = "".join(chunks).strip()
        if not assistant_text:
            raise HTTPException(status_code=502, detail={"error": "llm_error", "message": "Empty model response"})

        assistant_record = Message(
            id=uuid.uuid4(),
            thread_id=thread.id,
            role="assistant",
            content=assistant_text,
            created_at=ChatService._now_utc(),
        )

        if use_memory_fallback:
            ChatService._load_messages_from_store()
            ChatService._in_memory_messages_by_thread.setdefault(thread.id, []).append(assistant_record)
            ChatService._persist_messages_to_store()
        else:
            try:
                db.add(assistant_record)
                await db.commit()
            except Exception:
                ChatService._load_messages_from_store()
                ChatService._in_memory_messages_by_thread.setdefault(thread.id, []).append(assistant_record)
                ChatService._persist_messages_to_store()

        await ThreadService.auto_title_from_first_message(db, thread)
