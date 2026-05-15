# Backend — FastAPI + SQLAlchemy + LangChain

**Status**: ✅ Production-ready  
**Framework**: FastAPI + Uvicorn  
**Database**: PostgreSQL + SQLAlchemy 2.0  
**AI**: LangChain LCEL → LiteLLM proxy

---

## Quick Start

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env  # Update DATABASE_URL, LITELLM_API_KEY
uvicorn app.main:app --reload --port 8000
```

API available at `http://localhost:8000`  
Docs at `http://localhost:8000/docs`

## Architecture

### Layered Design

**Router → Service → Schema → Model**

- **API Routes** (`app/api/`): Parse request, call service, return response. No business logic.
- **Services** (`app/services/`): All business logic. Framework-agnostic, fully testable.
- **Schemas** (`app/schemas/`): Pydantic I/O validation. Separate from ORM models.
- **Models** (`app/models/`): SQLAlchemy ORM only. No methods or logic.

### Directory Structure

```
app/
├── api/
│   ├── auth.py           # Registration, login, logout, Google OAuth
│   ├── chat.py           # Send message, stream, attachments, list messages
│   ├── threads.py        # Create, list, rename, delete threads
│   ├── agents.py         # Research digest, Tic Tac Toe endpoints
│   └── deps.py           # Dependency injection (DB, auth)
├── services/
│   ├── auth_service.py   # User registration, login, JWT
│   ├── chat_service.py   # Message streaming, memory, persistence
│   ├── thread_service.py # Thread CRUD
│   ├── rag_service.py    # ChromaDB ingestion & retrieval
│   ├── image_service.py  # Gemini image generation
│   ├── sql_chat_service.py # NL-to-SQL generation + execution
│   ├── research_digest_service.py # arXiv search + LLM synthesis
│   ├── tic_tac_toe_service.py    # Game logic + minimax AI
│   └── attachment_service.py     # File upload & metadata
├── models/
│   ├── user.py           # User ORM
│   ├── thread.py         # Thread ORM
│   ├── message.py        # Message ORM
│   └── upload_metadata.py # File metadata ORM
├── schemas/
│   ├── auth.py           # RegisterRequest, LoginRequest
│   ├── chat.py           # ChatRequest, ChatResponse
│   ├── thread.py         # ThreadRequest, ThreadResponse
│   └── agents.py         # ResearchDigestRequest, TicTacToeRequest
├── ai/
│   ├── llm.py            # LiteLLM client singletons (ChatOpenAI, OpenAIEmbeddings)
│   ├── chains/           # LCEL chain definitions
│   ├── memory/           # Conversation memory utilities
│   ├── rag/              # ChromaDB client & ingestion
│   └── prompts/          # Prompt templates (.txt, .yaml)
├── core/
│   ├── config.py         # Settings from environment
│   ├── security.py       # bcrypt hash/verify, JWT encode/decode
│   └── logging.py        # App logging
├── db/
│   ├── session.py        # Async session factory
│   ├── base.py           # Base model for ORM
│   └── migrations/       # Alembic (database versioning)
└── main.py               # FastAPI app, router registration, startup hooks
```

## Key Conventions

### Auth
- **JWT in httpOnly cookies only** — never localStorage or response body
- **bcrypt hashing** with normalized 72-byte password truncation
- **Google OAuth 2.0** with account linking (one JWT layer for both)
- **get_current_user** dependency used in all protected routes

### AI Layer
- **All calls via LiteLLM proxy** at `litellm.amzur.com`
- **LCEL syntax only** (no LLMChain, SequentialChain)
- **Streaming on all user-facing responses** (never block)
- **user_email metadata** required on every LLM call for cost tracking

### Database
- **SQLAlchemy 2.0 style** (select(), mapped columns, async)
- **Alembic migrations only** — never direct DB changes
- **UUID primary keys** on all tables
- **DateTime(timezone=True)** on all timestamps
- **Per-user ChromaDB collections** (`user_{user_id}`) for RAG

### Error Handling
- **HTTPException with structured detail**:
  ```python
  raise HTTPException(
      status_code=404,
      detail={"error": "not_found", "message": "Resource not found"}
  )
  ```

## Testing

```bash
pytest -v  # Unit tests for services
```

Tests use `pytest` + `pytest-asyncio` + isolated test DB.

## API Examples

### Register
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'  
Response: {"user":{"id":"...","email":"user@example.com"}}
```

### Chat (Streaming SSE)
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"...","message":"Hello","attachment_ids":[],"response_mode":"llm"}'
# Returns SSE stream: data: {"token":"..."} \n\n
```

### NL-to-SQL
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"...","message":"Count users","response_mode":"sql"}'
# Generates, validates, executes SQL and streams results
```

### Research Digest (SSE)
```bash
curl -X POST http://localhost:8000/api/agents/research-digest/stream \
  -H "Content-Type: application/json" \
  -d '{"query":"machine learning","max_papers":5}'
# Streams structured digest token-by-token
``` (FastAPI)

## Run locally

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` at repo root and set values.
4. Start API server:
   - `uvicorn app.main:app --reload --port 8000`

API base URL: `http://localhost:8000`
