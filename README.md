# Amzur AI Chat

Monorepo with:
- `frontend/` React + TypeScript + Tailwind
- `backend/` FastAPI + SQLAlchemy + LangChain (LiteLLM proxy)

## 1) Configure environment

1. Copy `.env.example` to `.env` in repo root.
2. Fill required values (database, LiteLLM, auth, Google OAuth).
3. Optional frontend env: copy `frontend/.env.example` to `frontend/.env`.

## 2) Run backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 3) Run frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL: `http://localhost:5173`  
Backend default URL: `http://localhost:8000`

## 4) Features

### Core
- **Streaming chat** with LLM responses (token-by-token)
- **Multi-user support** with email/password and Google OAuth authentication
- **Thread management** with auto-generated titles and renaming
- **Conversation memory** - remembers last 5 exchanges per chat

### Advanced
- **Multi-modal attachments** - upload images, videos, CSV/Excel, LaTeX, code
- **Image generation** - generate images from text prompts (Gemini 2.0)
- **RAG with PDFs** - upload and chat about PDF documents using ChromaDB + embeddings
- **Persistent storage** - all data saved to PostgreSQL via Supabase
- **Secure auth** - JWT in httpOnly cookies, bcrypt password hashing

### Architecture
- **LiteLLM proxy** - all AI calls routed through `litellm.amzur.com`
- **LangChain LCEL** - language chains for flexible AI composition
- **React Query** - efficient server state management
- **Tailwind CSS** - responsive, dark-mode-ready UI
- **ChromaDB** - vector store for document embeddings

## 5) Environment variables

Copy `.env.example` to `.env` and configure:

```bash
# App
SECRET_KEY=your_secret_key
JWT_EXPIRE_MINUTES=480
APP_NAME=amzur-ai-chat
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname

# LiteLLM Proxy
LITELLM_PROXY_URL=https://litellm.amzur.com
LITELLM_API_KEY=sk-...
LLM_MODEL=gemini/gemini-2.5-flash
LITELLM_EMBEDDING_MODEL=text-embedding-3-large
IMAGE_GEN_MODEL=gemini/imagen-4.0-fast-generate-001

# Google OAuth (optional)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# File & Vector Storage
MAX_UPLOAD_MB=20
UPLOAD_DIR=./uploads
CHROMA_PERSIST_DIR=./chroma_db
CHAT_MEMORY_CONVERSATION_LIMIT=5
```

## 6) API Endpoints

### Auth
- `POST /api/auth/register` - Register with email/password
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/logout` - Logout and clear session
- `GET /api/auth/me` - Get current user
- `GET /api/auth/google/login` - Redirect to Google OAuth
- `GET /api/auth/google/callback` - Google OAuth callback

### Chat
- `GET /api/chat/{thread_id}/messages` - List messages in thread
- `POST /api/chat/stream` - Send message and stream response
- `POST /api/chat/generate-image` - Generate image from prompt
- `POST /api/chat/attachments` - Upload attachment file
- `GET /api/chat/attachments/{id}/download` - Download attachment

### Threads
- `GET /api/threads` - List user's threads
- `POST /api/threads` - Create new thread
- `PATCH /api/threads/{id}` - Rename thread
- `DELETE /api/threads/{id}` - Delete thread

## 7) Development

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Testing
Backend tests:
```bash
cd backend
pytest
```

### Database Migrations
```bash
cd backend
alembic upgrade head
```

## 8) Project Structure

```
/
├── frontend/              # React + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   ├── pages/        # Page-level components
│   │   ├── hooks/        # React hooks (useChat, useAuth, etc.)
│   │   ├── lib/          # API client, utilities
│   │   └── types/        # Shared TypeScript interfaces
│   └── vite.config.ts
│
├── backend/               # FastAPI + Python
│   ├── app/
│   │   ├── api/          # Route handlers (thin, no logic)
│   │   ├── services/     # Business logic layer
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response models
│   │   ├── ai/           # LLM chains, prompts, RAG, memory
│   │   ├── db/           # Database session, migrations
│   │   └── core/         # Settings, logging, config
│   ├── requirements.txt
│   └── main.py
│
├── .env.example          # Environment template
├── .github/
│   ├── copilot-instructions.md  # Development guidelines
│   └── project-description.md   # Project specifications
└── README.md
```
