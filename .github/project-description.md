Amzur AI Chat - Project Roadmap (Projects 1 to 11)

This document defines the full delivery scope for Amzur AI Chat across Projects 1 through 11.
It aligns with the architectural and operational rules in `.github/copilot-instructions.md`
and assumes all AI traffic flows only through the Amzur LiteLLM proxy.

Core platform rules
- All AI calls must route through `litellm.amzur.com`.
- Backend architecture must follow router -> service -> schema -> model separation.
- JWT must be stored only in an httpOnly cookie.
- All file uploads must be stored on disk, never as database blobs.
- All business logic belongs in backend services, not route handlers.
- All user-facing AI responses should stream when the experience benefits from it.


Project 1 - Foundation Chatbot (MVP)

Objective
- Build the first working version of the chatbot with a modern frontend, a FastAPI backend,
  and a streamed LLM response loop.

Scope
- Frontend: React + TypeScript + Tailwind chat application.
- Backend: FastAPI with structured folders for API, services, schemas, models, AI, and DB.
- AI orchestration: LangChain LCEL pipeline using prompt -> llm -> parser.
- Model access: `gemini/gemini-2.5-flash` or `gpt-4o` through LiteLLM only.
- Streaming: server-sent events from backend to frontend.

Key deliverables
- Chat input box, message list, and streamed assistant output.
- Backend endpoint for streaming responses.
- Shared frontend API client and typed request/response models.
- Environment-based configuration for model, database, auth, and proxy settings.

Acceptance criteria
- User can send a message and receive token-by-token streamed output.
- Backend boots from environment variables without hardcoded secrets.
- Routes remain thin and delegate logic to services.


Project 2 - Persistent Chat + Employee Login

Objective
- Add database persistence and employee authentication so users can return to prior chats.

Scope
- PostgreSQL with SQLAlchemy 2.0 and Alembic migrations.
- Email/password authentication for employees.
- JWT issuance and validation via secure httpOnly cookie.
- Persistent storage for users, threads, and messages.

Data model expectations
- `users`: UUID id, email, hashed_password, created_at.
- `threads`: UUID id, user_id, title, created_at, updated_at.
- `messages`: UUID id, thread_id, role, content, created_at.

Key deliverables
- Register, login, logout, and current-user endpoints.
- DB schema and migrations for auth and chat records.
- Message persistence for both user and assistant turns.
- Frontend hydration of previous messages after login.

Acceptance criteria
- Employee can register, log in, and receive a valid session cookie.
- Previous chat history reloads correctly for returning users.
- Passwords are hashed with bcrypt and never stored as plaintext.


Project 3 - Google OAuth + Thread Management

Objective
- Add Google sign-in and full thread lifecycle management.

Scope
- Google OAuth 2.0 login flow in backend.
- Account linking when Google email matches an existing user.
- Thread creation, listing, renaming, deletion, and ownership checks.
- Automatic thread naming from the first prompt.

Key deliverables
- `/auth/google/login` and `/auth/google/callback` endpoints.
- Thread CRUD endpoints and frontend sidebar support.
- Auto-title generation with fallback naming logic.

Acceptance criteria
- User can sign in with Google and receive the same JWT cookie structure.
- Thread operations are isolated per user.
- Thread list loads immediately after successful authentication.


Project 4 - Conversation Memory Window

Objective
- Make each chat remember the previous 5 user-assistant exchanges before generating the next answer.

Scope
- Store complete message history persistently.
- Retrieve only the previous 5 conversation pairs for LLM context.
- Make the limit configurable through environment variables.
- Support fallback in-memory persistence if database access fails.

Key deliverables
- Service method to retrieve the last N exchanges.
- Prompt assembly that injects only the configured memory window.
- `CHAT_MEMORY_CONVERSATION_LIMIT` environment setting.
- Tests for the memory limit behavior.

Acceptance criteria
- Only the previous 5 conversation pairs are used for LLM context by default.
- Full message history remains available for retrieval and auditing.
- Memory behavior survives thread switching and server restarts.


Project 5 - Multi-Modal Attachments

Objective
- Allow the chat window to accept images, videos, tables, code, formulas, and related file types as attachments.

Scope
- Frontend file picker with multiple uploads.
- Backend MIME validation and file size checks.
- Local disk storage for uploaded files.
- Metadata tracking including file path, MIME type, original filename, and classification.
- Attachment binding to a specific message.

Required storage behavior
- Uploaded files must be stored locally inside the codebase upload directory.
- Database metadata may store the physical path, but file content must not be stored in the database.
- If Supabase or another DB is used for metadata, `file_path` or `storage_path` must point to the local file.

File type classifications
- Image: `image/*`
- Video: `video/*`
- Table: `.csv`, `.xls`, `.xlsx`
- Code: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.cs`, `.go`, `.rs`
- Formula: `.tex`, `.latex`
- Document: `.pdf` and similar documents

Key deliverables
- Attachment upload and download endpoints.
- Attachment service for validation, classification, storage, and lookup.
- UI attachment chips and message rendering support.
- Prompt enrichment with attachment metadata.

Acceptance criteria
- Users can upload supported files and see them associated with chat messages.
- Files are stored on disk, not in DB blobs.
- Attachment metadata is retrievable and downloadable.


Project 6 - AI Image Generation

Objective
- Allow users to generate images from natural language prompts.

Scope
- Use the Gemini image generation model through LiteLLM.
- Store generated images locally in user-scoped folders.
- Return a downloadable asset and attach it to the thread when applicable.
- Present generation controls in the chat UI.

Key deliverables
- Image generation service wrapping the LiteLLM/OpenAI-compatible client.
- Endpoint for prompt submission and result retrieval.
- Generated image attachment registration and download support.
- Frontend prompt UI and image preview behavior.

Acceptance criteria
- User can submit a prompt and receive a generated image.
- Generated images persist on disk and can be downloaded later.
- Usage attribution includes the authenticated user email.


Project 7 - PDF RAG Chat

Objective
- Let users upload PDF files and ask questions grounded in document content.

Scope
- PDF text extraction using `pypdf`.
- Text chunking and embedding generation.
- Per-user ChromaDB collections persisted to disk.
- Retrieval of relevant chunks before answer generation.
- Prompt injection of retrieved context.

Key deliverables
- PDF ingestion service.
- ChromaDB persistence and retrieval helpers.
- Embeddings through LiteLLM using `text-embedding-3-large`.
- PDF-aware upload flow and RAG-enhanced answer path.

Acceptance criteria
- Users can upload PDFs and later ask questions about them.
- Retrieved document context is incorporated into the assistant response.
- User document isolation is enforced.


Project 8 - Natural Language to SQL

Objective
- Allow users to connect to the application database and ask questions in natural language that map to SQL-style analysis.

Scope
- Generate SQL from a natural-language prompt.
- Use a schema snapshot to improve SQL generation quality.
- Enforce read-only safety rules.
- Execute valid SQL and render results back to the user.

Safety requirements
- Unsafe keywords must be blocked case-insensitively.
- At minimum block: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`.
- SQL generation must never bypass validation.

Key deliverables
- SQL chat service that generates, validates, executes, and formats results.
- Response mode or endpoint for SQL-backed chat.
- Helpful no-results and error handling behavior.

Acceptance criteria
- User can ask common data questions in natural language.
- System generates only validated read-only SQL.
- Results stream or render clearly back into the chat experience.


Project 9 - CSV / Google Sheets Query Agent

Objective
- Build a FastAPI endpoint that loads a `.csv`, `.xls`, or `.xlsx` file, or a Google Sheet,
  into a Pandas DataFrame and answers natural-language questions using a LangChain Pandas dataframe agent backed by an LLM.

Scope
- Data source 1: uploaded local CSV or Excel file.
- Data source 2: Google Sheet loaded through Google Sheets API.
- Use Pandas DataFrame as the working data structure.
- Use LangChain dataframe agent for natural-language reasoning over the table.
- Return both the answer and intermediate reasoning artifacts useful for debugging.

Implementation expectations
- FastAPI endpoint under the authenticated API surface.
- Request must accept either an uploaded file reference or a Google Sheet identifier/URL.
- Google Sheets access must use service account credentials from environment configuration.
- Agent creation must use the LiteLLM-backed LLM client, not a direct vendor client.
- `return_intermediate_steps=True` should be enabled so generated code or reasoning can be surfaced.

Key deliverables
- Request and response schemas for dataframe queries.
- Backend service to resolve file input or Google Sheet input into a DataFrame.
- Pandas dataframe agent invocation with user metadata attached.
- Clear response including answer, source details, row and column counts, and intermediate steps.

Acceptance criteria
- User can query a CSV or Excel attachment in natural language.
- User can query a Google Sheet in natural language.
- Response is grounded in the DataFrame contents.
- Configuration uses environment-based Google service account credentials.


Project 10 - Research Digest Agent

Objective
- Build an agent that searches research sources and produces a structured digest for a user-specified topic.

Scope
- Search arXiv for relevant papers.
- Collect and deduplicate evidence across multiple query variants.
- Use the LLM to synthesize a structured research digest.
- Stream output back to the client.

Key deliverables
- Research digest request schema.
- Agent endpoint for streamed digest generation.
- Service that handles source search, evidence gathering, synthesis, and fallback behavior.

Acceptance criteria
- User can request a topic digest and receive a streamed structured summary.
- Network or upstream failures degrade gracefully with fallback output.


Project 11 - Tic Tac Toe Agent

Objective
- Add a simple game agent that lets the user play Tic Tac Toe against the system.

Scope
- Validate moves and maintain board state.
- Detect wins, losses, and draws.
- Implement AI response logic using minimax or equivalent deterministic strategy.
- Expose the game through a FastAPI endpoint and frontend panel.

Key deliverables
- Tic Tac Toe request and response schemas.
- Game service containing board evaluation and AI move logic.
- API route returning updated board state and status.

Acceptance criteria
- User can make a move and receive a valid AI response move.
- Game state is consistently enforced.
- Win and draw conditions are correctly reported.


Cross-project non-functional requirements

Architecture and code quality
- Follow router -> service -> schema -> model separation.
- Keep AI logic under backend `app/ai` and `app/services`.
- Use strict TypeScript and typed Python functions.
- Add tests where practical for each project slice.

Security
- JWT stored only in httpOnly cookie.
- Validate request payloads with Pydantic.
- No hardcoded secrets, model keys, or provider endpoints.
- Preserve user-level access isolation for threads, files, and vector collections.

Operational constraints
- LiteLLM proxy is mandatory for chat, embeddings, SQL agents, dataframe agents, and image generation.
- Environment config must remain boot-safe when optional services are absent.
- Structured error responses should be used for API failures.


Suggested execution order
1. Project 1: foundation chat experience.
2. Project 2: persistence and employee authentication.
3. Project 3: Google OAuth and thread lifecycle.
4. Project 4: conversation memory window.
5. Project 5: multi-modal attachments.
6. Project 6: image generation.
7. Project 7: PDF RAG.
8. Project 8: natural-language SQL.
9. Project 9: CSV / Google Sheets dataframe agent.
10. Project 10: research digest agent.
11. Project 11: Tic Tac Toe agent.

Each project should be independently testable and should preserve the architectural constraints listed above.