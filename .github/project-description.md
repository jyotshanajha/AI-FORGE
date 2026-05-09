Amzur AI Chat - 3 Project Development Plan

This document expands the three project stages into complete development descriptions.
It aligns with the architecture and engineering rules in `.github/copilot-instructions.md`
and the initial setup objective in `.github/project-ai-forge.md`.

Note on model access:
- Gemini can be used, but all AI calls must go through the Amzur LiteLLM proxy.
- Do not call provider APIs directly from frontend or backend business code.

Project 1 - Foundation Chatbot (MVP)

Objective
- Build a working chatbot with a modern frontend and Python backend that can send a user
	message to an LLM and stream back the assistant response.

Scope
- Frontend: React + TypeScript + Tailwind app with chat page and input box.
- Backend: FastAPI app with layered structure (api/services/schemas/models/ai).
- AI orchestration: LangChain LCEL pipeline (`prompt | llm | parser`).
- LLM: `gemini/gemini-2.5-flash` (or `gpt-4o`) through LiteLLM proxy only.
- Config: environment-driven settings (`.env`), no hardcoded secrets.
- Streaming: server-sent events from backend; token-by-token rendering in frontend.

Key deliverables
- End-to-end chat flow:
	frontend input -> backend route -> service -> AI chain -> streamed response.
- Scaffolded repository structure for both frontend and backend.
- `requirements.txt`, `.env.example`, and startup-ready app entry points.
- Shared API client file on frontend (`src/lib/api.ts`) and shared types file (`src/types`).

Acceptance criteria
- User can open chat UI and receive streamed LLM output for each prompt.
- All AI requests use `LITELLM_PROXY_URL` and `LITELLM_API_KEY` from environment.
- No feature logic in routers; business logic in services.
- No secrets in code or committed config.


Project 2 - Persistent Chat + Employee Login

Objective
- Add persistence and internal authentication so employee users can log in and see
	their historical chats.

Scope
- Database: Supabase PostgreSQL (implemented via SQLAlchemy 2.0 + Alembic).
- Persistence: store users, chats, messages, and timestamps in UTC.
- Auth strategy: email/password login for Amzur employees with JWT in httpOnly cookie.
- Retrieval: when user logs in, load previous chats/messages into UI.
- App state: use React Query for server data loading and caching.

Data model expectations
- `users`: UUID id, email (unique), hashed_password, created_at.
- `threads`: UUID id, user_id FK, title, created_at, updated_at.
- `messages`: UUID id, thread_id FK, role (user/assistant), content, created_at.

Key deliverables
- Migration scripts for DB schema and indexes.
- Auth endpoints (register/login/logout/me) with cookie-based session handling.
- Chat persistence service that saves both user and assistant messages.
- Initial thread/message fetch API to hydrate chat window after login.

Acceptance criteria
- Employee can register/login and receive authenticated session cookie.
- Returning user sees previously stored chats loaded from database.
- Passwords are hashed with bcrypt and never stored in plaintext.
- DB access is service-layer only; routes remain thin.


Project 3 - Google OAuth + Thread Management

Objective
- Add Google login and full thread lifecycle management with automatic thread naming.

Scope
- Google OAuth 2.0 integration in backend auth service.
- Account linking: if Google email matches existing account, link by updating `google_id`.
- Thread CRUD: create, rename, update metadata, delete.
- Auto-title: generate thread name from first user message.
- Session boot: load all user threads on login and allow switching threads.

Key deliverables
- OAuth routes (`/auth/google/login`, `/auth/google/callback`) issuing same JWT cookie
	structure used by email/password flow.
- Thread APIs with ownership checks to prevent cross-user access.
- Frontend thread sidebar with create/select/rename/delete actions.
- Auto-generated title logic with fallback title format
	(example: `New Chat - YYYY-MM-DD`) when AI or heuristic title generation fails.

Acceptance criteria
- User can authenticate with Google and access same chat system.
- Threads can be created, updated, deleted, and listed correctly per user.
- Thread list loads immediately after successful login.
- Auto thread naming works on first message and can be edited by user.


Cross-project non-functional requirements

Architecture and code quality
- Follow router -> service -> schema -> model separation.
- Keep AI logic under backend `app/ai` and `app/services`.
- Use strict TypeScript and typed Python functions.
- Add unit/integration tests per project increment.

Security
- JWT stored only in httpOnly cookie.
- Validate all request payloads with Pydantic schemas.
- No hardcoded API keys, secrets, or model endpoints.

Operational constraints
- LiteLLM proxy (`litellm.amzur.com`) is mandatory for AI calls.
- Use environment-specific config and keep `.env.example` up to date.
- Handle errors with structured API responses.


Suggested execution order
1. Complete Project 1 scaffolding + streaming chatbot.
2. Add Project 2 persistence + employee auth.
3. Add Project 3 Google OAuth + thread lifecycle.

Each phase should be independently testable and releasable.