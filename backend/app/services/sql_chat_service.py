import asyncio
import re
from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy import create_engine, text

from app.ai.llm import llm
from app.core.config import settings


SQL_GENERATION_PROMPT = """You are a PostgreSQL SQL generator.
Given a database schema and a user question, produce exactly one read-only SQL query.
Rules:
- Output SQL only. No markdown fences, no explanation.
- Use PostgreSQL syntax.
- Prefer schema-qualified names only if needed.
- Never generate INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER, CREATE, GRANT, REVOKE.
- Keep queries safe and read-only.
- If the user asks for table columns, query information_schema.columns.
- If the user mentions chat_messages, use the actual table name messages.
"""

FORBIDDEN_SQL_KEYWORDS = ("INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER")
UUID_PATTERN = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)


def _build_sync_db_url(database_url: str) -> str:
    """Build a sync SQLAlchemy URL for SQL execution from async settings.DATABASE_URL."""
    if database_url.startswith("postgresql+asyncpg://"):
        sync_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    elif database_url.startswith("postgresql+psycopg://"):
        sync_url = database_url.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1)
    elif database_url.startswith("postgresql+psycopg2://"):
        sync_url = database_url
    elif database_url.startswith("postgresql://"):
        sync_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    elif database_url.startswith("postgres://"):
        sync_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    else:
        sync_url = database_url

    parsed = urlparse(sync_url)
    query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query_params.pop("pgbouncer", None)
    rebuilt = parsed._replace(query=urlencode(query_params))
    return urlunparse(rebuilt)


def _normalize_sql(sql: str) -> str:
    sql_clean = sql.strip()
    sql_clean = re.sub(r"^```(?:sql)?", "", sql_clean, flags=re.IGNORECASE).strip()
    sql_clean = re.sub(r"```$", "", sql_clean).strip()
    return sql_clean.rstrip(";")


def _validate_read_only_sql(sql: str) -> tuple[bool, str | None]:
    normalized = _normalize_sql(sql)

    if not normalized:
        return False, "Generated SQL is empty."

    if not re.match(r"^\s*(SELECT|WITH)\b", normalized, flags=re.IGNORECASE):
        return False, "Only read-only SELECT queries are allowed."

    for keyword in FORBIDDEN_SQL_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return False, f"Blocked unsafe SQL keyword: {keyword}."

    return True, None


def _load_schema_snapshot(sync_db_url: str) -> str:
    engine = create_engine(sync_db_url, pool_pre_ping=True)
    schema_query = text(
        """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
        """
    )

    grouped: dict[str, list[str]] = {}
    with engine.connect() as conn:
        rows = conn.execute(schema_query).fetchall()
    engine.dispose()

    for table_name, column_name, data_type in rows:
        grouped.setdefault(str(table_name), []).append(f"{column_name} ({data_type})")

    lines: list[str] = []
    for table_name, columns in grouped.items():
        lines.append(f"{table_name}: " + ", ".join(columns))

    return "\n".join(lines)


def _execute_query(sync_db_url: str, sql: str) -> tuple[list[str], list[tuple]]:
    engine = create_engine(sync_db_url, pool_pre_ping=True)
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        rows = result.fetchmany(50)
        columns = list(result.keys())
    engine.dispose()
    return columns, rows


def _extract_first_uuid(text_value: str) -> str | None:
    match = UUID_PATTERN.search(text_value)
    return match.group(0) if match else None


def _find_rows_by_id_across_tables(
    sync_db_url: str,
    target_id: str,
) -> list[tuple[str, list[str], list[tuple]]]:
    engine = create_engine(sync_db_url, pool_pre_ping=True)
    table_query = text(
        """
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND column_name = 'id'
        ORDER BY table_name
        """
    )

    matches: list[tuple[str, list[str], list[tuple]]] = []
    with engine.connect() as conn:
        table_rows = conn.execute(table_query).fetchall()
        for (table_name_raw,) in table_rows:
            table_name = str(table_name_raw)
            lookup_query = text(f'SELECT * FROM "{table_name}" WHERE id::text = :target_id LIMIT 5')
            result = conn.execute(lookup_query, {"target_id": target_id})
            rows = result.fetchall()
            if rows:
                matches.append((table_name, list(result.keys()), rows))

    engine.dispose()
    return matches


def _format_sql_result(sql: str, columns: list[str], rows: list[tuple]) -> str:
    if not rows:
        return f"Generated SQL:\n{sql}\n\nNo rows returned."

    header = " | ".join(columns)
    separator = " | ".join(["---"] * len(columns))

    body_lines = []
    for row in rows:
        rendered = [str(value) if value is not None else "NULL" for value in row]
        body_lines.append(" | ".join(rendered))

    preview = "\n".join(body_lines)
    return (
        f"Generated SQL:\n{sql}\n\n"
        f"Result preview (up to 50 rows):\n"
        f"{header}\n{separator}\n{preview}"
    )


def _format_cross_table_matches(target_id: str, matches: list[tuple[str, list[str], list[tuple]]]) -> str:
    if not matches:
        return f"No rows found for id {target_id} in public tables with an id column."

    blocks: list[str] = [f"No rows in the originally generated query. Found matches for id {target_id}:"]
    for table_name, columns, rows in matches:
        header = " | ".join(columns)
        separator = " | ".join(["---"] * len(columns))
        rendered_rows = []
        for row in rows:
            rendered = [str(value) if value is not None else "NULL" for value in row]
            rendered_rows.append(" | ".join(rendered))
        blocks.append(
            f"\nTable: {table_name}\n{header}\n{separator}\n" + "\n".join(rendered_rows)
        )

    return "\n".join(blocks)


async def _generate_sql(question: str, schema_snapshot: str, user_email: str) -> str:
    if llm is None:
        raise RuntimeError("LLM is unavailable.")

    prompt = (
        f"{SQL_GENERATION_PROMPT}\n\n"
        f"Schema:\n{schema_snapshot}\n\n"
        f"User question:\n{question}\n"
    )
    response = await llm.ainvoke(
        prompt,
        config={"metadata": {"user_email": user_email}},
    )
    content = response.content if hasattr(response, "content") else str(response)
    return _normalize_sql(str(content))


class SQLChatService:
    @staticmethod
    async def stream_sql_reply(question: str, user_email: str) -> AsyncGenerator[str, None]:
        if not settings.DATABASE_URL:
            yield "Database is not configured. Set DATABASE_URL in the backend environment."
            return

        if llm is None:
            yield "AI service is unavailable for SQL mode right now."
            return

        try:
            sync_db_url = _build_sync_db_url(settings.DATABASE_URL)
            schema_snapshot = await asyncio.to_thread(_load_schema_snapshot, sync_db_url)
            generated_sql = await _generate_sql(question, schema_snapshot, user_email)
            is_valid, error = _validate_read_only_sql(generated_sql)
            if not is_valid:
                yield f"SQL mode blocked an unsafe query. {error}"
                return

            columns, rows = await asyncio.to_thread(_execute_query, sync_db_url, generated_sql)
            full_response = _format_sql_result(generated_sql, columns, rows)
            if not rows:
                extracted_id = _extract_first_uuid(generated_sql) or _extract_first_uuid(question)
                if extracted_id:
                    matches = await asyncio.to_thread(_find_rows_by_id_across_tables, sync_db_url, extracted_id)
                    full_response = full_response + "\n\n" + _format_cross_table_matches(extracted_id, matches)
            for chunk in full_response:
                yield chunk
        except Exception as exc:
            yield f"SQL mode failed: {exc}"
