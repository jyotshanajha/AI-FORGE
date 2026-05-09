import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.thread import Thread
from app.models.user import User
from app.services.fallback_store import get_store, update_store


class ThreadService:
    _in_memory_threads_by_user_email: dict[str, list[Thread]] = {}

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _load_threads_from_store() -> None:
        if ThreadService._in_memory_threads_by_user_email:
            return

        store = get_store()
        raw_threads = store.get("threads_by_user_email", {})
        if not isinstance(raw_threads, dict):
            return

        loaded: dict[str, list[Thread]] = {}
        for email, rows in raw_threads.items():
            if not isinstance(email, str) or not isinstance(rows, list):
                continue
            user_threads: list[Thread] = []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                try:
                    user_threads.append(
                        Thread(
                            id=uuid.UUID(row["id"]),
                            user_id=uuid.UUID(row["user_id"]),
                            title=row.get("title") or "New Chat",
                            created_at=datetime.fromisoformat(row["created_at"]),
                            updated_at=datetime.fromisoformat(row["updated_at"]),
                        )
                    )
                except Exception:
                    continue
            loaded[email] = user_threads

        ThreadService._in_memory_threads_by_user_email = loaded

    @staticmethod
    def _persist_threads_to_store() -> None:
        serializable: dict[str, list[dict[str, str]]] = {}
        for email, threads in ThreadService._in_memory_threads_by_user_email.items():
            serializable[email] = [
                {
                    "id": str(t.id),
                    "user_id": str(t.user_id),
                    "title": t.title,
                    "created_at": (t.created_at or ThreadService._now_utc()).isoformat(),
                    "updated_at": (t.updated_at or ThreadService._now_utc()).isoformat(),
                }
                for t in threads
            ]

        def _mutator(store: dict) -> None:
            store["threads_by_user_email"] = serializable

        update_store(_mutator)

    @staticmethod
    def _list_memory_threads(user_email: str) -> list[Thread]:
        ThreadService._load_threads_from_store()
        threads = ThreadService._in_memory_threads_by_user_email.get(user_email, [])
        return sorted(threads, key=lambda t: t.updated_at or ThreadService._now_utc(), reverse=True)

    @staticmethod
    def _get_memory_thread(user_email: str, thread_id: uuid.UUID) -> Thread | None:
        ThreadService._load_threads_from_store()
        for thread in ThreadService._in_memory_threads_by_user_email.get(user_email, []):
            if thread.id == thread_id:
                return thread
        return None

    @staticmethod
    async def list_threads(db: AsyncSession, user: User) -> list[Thread]:
        try:
            result = await db.execute(select(Thread).where(Thread.user_id == user.id).order_by(Thread.updated_at.desc()))
            return list(result.scalars().all())
        except Exception:
            return ThreadService._list_memory_threads(user.email)

    @staticmethod
    async def create_thread(db: AsyncSession, user: User, title: str | None = None) -> Thread:
        try:
            thread = Thread(user_id=user.id, title=title or "New Chat")
            db.add(thread)
            await db.commit()
            await db.refresh(thread)
            return thread
        except Exception:
            now = ThreadService._now_utc()
            thread = Thread(
                id=uuid.uuid4(),
                user_id=user.id,
                title=title or "New Chat",
                created_at=now,
                updated_at=now,
            )
            ThreadService._load_threads_from_store()
            user_threads = ThreadService._in_memory_threads_by_user_email.setdefault(user.email, [])
            user_threads.insert(0, thread)
            ThreadService._persist_threads_to_store()
            return thread

    @staticmethod
    async def get_thread_or_404(db: AsyncSession, user: User, thread_id: uuid.UUID) -> Thread:
        thread: Thread | None
        try:
            result = await db.execute(select(Thread).where(Thread.id == thread_id, Thread.user_id == user.id))
            thread = result.scalar_one_or_none()
        except Exception:
            thread = ThreadService._get_memory_thread(user.email, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Thread not found"})
        return thread

    @staticmethod
    async def update_thread_title(db: AsyncSession, thread: Thread, title: str) -> Thread:
        thread.title = title
        try:
            await db.commit()
            await db.refresh(thread)
        except Exception:
            thread.updated_at = ThreadService._now_utc()
            ThreadService._load_threads_from_store()
            for email, threads in ThreadService._in_memory_threads_by_user_email.items():
                for idx, candidate in enumerate(threads):
                    if candidate.id == thread.id:
                        threads[idx] = thread
                        ThreadService._persist_threads_to_store()
                        return thread
        return thread

    @staticmethod
    async def delete_thread(db: AsyncSession, thread: Thread) -> None:
        try:
            await db.delete(thread)
            await db.commit()
            return
        except Exception:
            pass

        ThreadService._load_threads_from_store()
        for email, threads in ThreadService._in_memory_threads_by_user_email.items():
            filtered = [t for t in threads if t.id != thread.id]
            if len(filtered) != len(threads):
                ThreadService._in_memory_threads_by_user_email[email] = filtered
                ThreadService._persist_threads_to_store()
                break

    @staticmethod
    async def auto_title_from_first_message(db: AsyncSession, thread: Thread) -> None:
        try:
            result = await db.execute(
                select(Message).where(Message.thread_id == thread.id, Message.role == "user").order_by(Message.created_at.asc())
            )
            first_user_message = result.scalar_one_or_none()
        except Exception:
            return
        if not first_user_message:
            return
        if thread.title != "New Chat":
            return

        words = first_user_message.content.strip().split()
        title = " ".join(words[:8]).strip() or "New Chat"
        thread.title = title
        try:
            await db.commit()
        except Exception:
            thread.updated_at = ThreadService._now_utc()
            ThreadService._load_threads_from_store()
            for email, threads in ThreadService._in_memory_threads_by_user_email.items():
                for idx, candidate in enumerate(threads):
                    if candidate.id == thread.id:
                        threads[idx] = thread
                        ThreadService._persist_threads_to_store()
                        return
