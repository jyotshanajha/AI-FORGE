from collections.abc import AsyncGenerator
import logging
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_async_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg://"):
        async_url = database_url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql+asyncpg://"):
        async_url = database_url
    elif database_url.startswith("postgresql://"):
        async_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        async_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    else:
        async_url = database_url

    parsed = urlparse(async_url)
    query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query_params.pop("pgbouncer", None)
    sslmode = query_params.pop("sslmode", None)
    if sslmode and "ssl" not in query_params:
        query_params["ssl"] = sslmode

    rebuilt = parsed._replace(query=urlencode(query_params))
    return urlunparse(rebuilt)


try:
    async_database_url = _build_async_database_url(settings.DATABASE_URL)
    engine_kwargs = {"pool_pre_ping": True}
    if async_database_url.startswith("postgresql+asyncpg://"):
        # Supabase pooler (pgBouncer transaction mode) is incompatible with asyncpg statement caching.
        engine_kwargs["connect_args"] = {"statement_cache_size": 0}

    engine = create_async_engine(async_database_url, **engine_kwargs)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
except Exception as e:
    logger.warning(f"Failed to create database engine: {e}. Using fallback mode.")
    engine = None
    SessionLocal = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if SessionLocal is None:
        raise RuntimeError("Database connection not available")
    async with SessionLocal() as session:
        yield session
