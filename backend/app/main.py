import logging
import sys
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.threads import router as thread_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
import app.models.message  # noqa: F401
import app.models.thread  # noqa: F401
import app.models.user  # noqa: F401


logger = logging.getLogger(__name__)

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    try:
        if engine is not None:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
    except SQLAlchemyError as exc:
        logger.warning("Database unavailable during startup: %s", exc)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(thread_router, prefix="/api/threads", tags=["threads"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
