import json
import uuid
from datetime import datetime, timezone
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user
from app.main import app
from app.models.user import User
from app.services.research_digest_service import ResearchDigestService


@pytest.mark.asyncio
async def test_research_digest_stream_sse_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_stream_digest(*_args: Any, **_kwargs: Any):
        yield {"type": "status", "message": "Starting autonomous arXiv search..."}
        yield {"type": "meta", "query": "rag systems", "papers_found": 3}
        yield {"type": "token", "token": "# Research Digest"}
        yield {"type": "error", "message": "Synthetic error for contract validation"}

    async def override_current_user() -> User:
        return User(
            id=uuid.uuid4(),
            email="stream.test@example.com",
            hashed_password=None,
            created_at=datetime.now(timezone.utc),
        )

    monkeypatch.setattr(ResearchDigestService, "stream_digest", fake_stream_digest)
    app.dependency_overrides[get_current_user] = override_current_user

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/agents/research-digest/stream",
                json={"query": "rag systems", "max_papers": 3},
            )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

        payload_lines = [
            line for line in response.text.splitlines() if line.startswith("data: ")
        ]
        assert payload_lines, "Expected at least one SSE data line"
        assert payload_lines[-1] == "data: [DONE]"

        parsed_events: list[dict[str, Any]] = []
        for line in payload_lines[:-1]:
            parsed_events.append(json.loads(line[len("data: ") :]))

        event_types = {event.get("type") for event in parsed_events}
        assert event_types >= {"status", "meta", "token", "error"}
    finally:
        app.dependency_overrides.pop(get_current_user, None)
