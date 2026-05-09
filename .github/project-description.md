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



Project 4: Allow every chat to have a memory of 5 prevoious conversations.  That is, the chat should remember the previous 5 conversations in the chat before answering

Project 5: ALlow the chat window to input images, videos. tables, formulas, code as attachments

Project 6: Allow the chat to create images.  Use Google gemini 2.0 Image Generation model

Project 7:  Upload a file into the chat and chat about the file.  Lets start with PDF.  Use RAG framework.  Use ChromaDB for vector storage, OpenAI Embeddings Large for embeddings


Project 4 - Conversation Memory Window (5-Turn Limit)

Objective
- Enable every chat to remember the previous 5 user-assistant conversation pairs before answering.

Scope
- Memory management: store full conversation history in DB; retrieve only last 5 exchanges for LLM context.
- LLM integration: inject limited history into LCEL chain.
- Configuration: make memory limit configurable via `CHAT_MEMORY_CONVERSATION_LIMIT` env var.
- Fallback: if DB fails, use in-memory JSON store as backup.

Key deliverables
- `get_last_n_conversations()` method in `ChatService` that retrieves previous 5 turns.
- History formatting for LCEL chain: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]`.
- Environment variable `CHAT_MEMORY_CONVERSATION_LIMIT=5` in `.env` and `.env.example`.
- Tests confirming memory window includes only 5 exchanges (10 messages) before each LLM call.

Acceptance criteria
- Chat remembers and uses only the last 5 conversation pairs for LLM context.
- Full history is persisted in DB for audit/retrieval.
- Memory limit is configurable and defaults to 5.
- Conversation continues correctly across thread switches and server restarts.


Project 5 - Multi-Modal Attachments (Images, Videos, Tables, Code)

Objective
- Allow users to upload and reference multiple file types (images, videos, CSV/Excel, LaTeX, code) in chat.

Scope
- File upload: UI file picker accepting specified MIME types.
- Validation: server-side MIME type checking; file size limits (`MAX_UPLOAD_MB`).
- Storage: files saved to disk with UUID-based filenames; metadata stored in fallback store.
- Attachment binding: link uploaded files to specific messages.
- Rendering: display attachment chips in message bubbles with download links.
- LLM context: include attachment metadata (filename, type, size) in prompt.

File type classifications
- Image: `image/*` → `attachment_type="image"`
- Video: `video/*` → `attachment_type="video"`
- Table: `.csv`, `.xls`, `.xlsx` → `attachment_type="table"`
- Code: `.py`, `.js`, `.ts`, `.java`, etc. → `attachment_type="code"`
- Formula: `.tex`, `.latex` → `attachment_type="formula"`
- Document: `.pdf`, other → `attachment_type="document"`

Key deliverables
- `AttachmentService` with upload/validation/binding logic.
- API endpoints: `POST /api/chat/attachments` (upload), `GET /api/chat/attachments/{id}/download` (retrieve).
- Schema: `ChatAttachment` with id, filename, mime_type, size_bytes, attachment_type, download_url.
- Frontend: file input UI in `InputBar`, attachment chips, inline rendering in message bubbles.
- Configured MIME types in `settings.ALLOWED_ATTACHMENT_MIME_TYPES`.

Acceptance criteria
- Users can upload multiple files of supported types.
- Files are stored securely with metadata tracking.
- Attachments appear in chat UI and can be downloaded.
- LLM is aware of attached file metadata when generating responses.
- File size and type restrictions are enforced.


Project 6 - Image Generation (Gemini 2.0)

Objective
- Enable users to generate images from text prompts using Google Gemini 2.0 image generation model.

Scope
- Image generation: LLM receives text prompt, returns generated image via LiteLLM proxy.
- Storage: generated images saved to disk in user-specific directory.
- UI: "Generate Image" button in chat input bar opens dialog for prompt entry.
- Integration: generated images appear as attachments in message thread.
- Error handling: graceful fallback if image generation fails.

Key deliverables
- `ImageService` class wrapping LiteLLM image generation API.
- API endpoint: `POST /api/chat/generate-image` accepting `{prompt, thread_id}`.
- Response schema: `ImageGenerationResponse` with url, filename, mime_type, original_prompt, size_bytes.
- Frontend component: "Generate Image" button, dialog with prompt input, image preview on success.
- Configured model: `IMAGE_GEN_MODEL=gemini/imagen-4.0-fast-generate-001` (via LiteLLM proxy).

Image storage
- Directory: `{UPLOAD_DIR}/generated/{user_id}/`
- Filename format: `generated_{TIMESTAMP}.png`
- Access: `/api/chat/attachments/generated/{user_id}/{filename}` download endpoint.

Key deliverables (continued)
- Error handling: HTTP 502 if image generation fails, with descriptive error message.
- Usage tracking: all image generation calls include `user=current_user.email` for cost attribution.
- Metadata: original prompt stored in response for audit trail.

Acceptance criteria
- User can enter image prompt in dialog and receive generated image.
- Generated images are stored persistently and accessible via download URL.
- Image generation errors are caught and reported to user.
- Generated images can be sent as context to the chat or used separately.
- Model and API key come from environment variables only.


Project 7 - RAG with PDF Upload (ChromaDB + Embeddings)

Objective
- Enable users to upload PDF documents and ask questions about their content using Retrieval-Augmented Generation (RAG).

Scope
- PDF handling: extract text from uploaded PDFs.
- Vectorization: split text into chunks and embed with OpenAI embeddings via LiteLLM.
- Vector store: ChromaDB persisted to disk with per-user collections.
- Retrieval: search uploaded documents for context relevant to user query.
- LLM integration: inject retrieved context into chat prompt before generating response.
- Isolation: per-user document collections prevent cross-user document retrieval.

Key deliverables
- `RAGService` class handling PDF ingestion and vector retrieval.
- PDF extraction: use `pypdf` library to extract text from pages.
- Text splitting: `RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=256)`.
- ChromaDB client: persistent collection per user named `user_{user_id}`.
- Embeddings: OpenAI `text-embedding-3-large` via LiteLLM proxy.
- Retrieval logic: `retrieve_context(user_id, query, top_k=5)` returns top 5 relevant chunks.

API & storage
- Existing `POST /api/chat/attachments` extended to detect PDFs and trigger ingestion.
- PDF ingestion runs in background (via FastAPI `BackgroundTasks`).
- Storage location: `{UPLOAD_DIR}/{user_id}/{attachment_id}_{filename}`
- Vector store: `{CHROMA_PERSIST_DIR}/` with collections per user.

Chat integration
- When user sends message: retrieve relevant document chunks from ChromaDB.
- Inject context into prompt: "Context from your documents: [chunks]".
- Seamless fallback: if RAG retrieval fails, chat continues without context.

Key deliverables (continued)
- Error handling: PDF extraction errors logged but don't block attachment upload.
- Cleanup: `delete_user_documents(user_id)` removes all user data if account deleted.
- Metadata: chunk index, source filename, page numbers included in ChromaDB records.

Configuration
- `CHROMA_PERSIST_DIR=./chroma_db` (default).
- `LITELLM_EMBEDDING_MODEL=text-embedding-3-large` for vectorization.
- PDF support in `ALLOWED_ATTACHMENT_MIME_TYPES`: `application/pdf`, `application/x-pdf`.

Acceptance criteria
- Users can upload PDFs and see them classified as "document" attachment type.
- Chat references uploaded PDFs when answering questions.
- Retrieved context is accurate and relevant to user query.
- Per-user document isolation prevents information leakage.
- PDF ingestion completes without blocking chat functionality.
- Vector storage persists across server restarts.