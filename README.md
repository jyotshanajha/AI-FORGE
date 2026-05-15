# Amzur AI Chat — Full-Featured Conversational AI Platform

**Status**: ✅ All 11 projects complete • All features tested and verified

## Overview

Amzur AI Chat is a production-ready, multi-user conversational AI platform with:
- **React 18+ TypeScript** frontend (Vite, Tailwind CSS)
- **FastAPI Python 3.11+** backend (SQLAlchemy, LangChain, LiteLLM)
- **PostgreSQL** persistent storage with JWT authentication
- **Advanced features**: RAG (ChromaDB), image generation, NL-to-SQL, agents (research digest, Tic Tac Toe)

## Quick Start

### Prerequisites
- Python 3.11+ (backend)
- Node.js 18+ (frontend)
- PostgreSQL database (local or Supabase)
- LiteLLM proxy API key (internal `litellm.amzur.com`)

### Backend Setup

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Update DATABASE_URL and LITELLM_API_KEY
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Access at:
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Core Features

### 🔐 Authentication
- **Email/password** with bcrypt hashing
- **Google OAuth 2.0** account linking
- **JWT in httpOnly cookies** (XSS-safe)
- **Multi-user** isolated sessions

### 💬 Chat & Streaming
- **Token-by-token streaming** responses via SSE
- **Conversation memory** (persistent last 5 exchanges)
- **Thread-based organization** with auto-titling
- **LiteLLM proxy routing** (gpt-4o, Gemini 2.5 Flash)

### 📎 Multi-Modal Support
- **Image upload & storage** (JPG, PNG, WebP)
- **PDF RAG** via ChromaDB embeddings
- **CSV/Excel analysis** via NL queries
- **Code & LaTeX rendering** in chat

### 🎨 Advanced Agents
- **Project 8**: NL-to-SQL chat (read-only, safe keyword blocks)
- **Project 10**: Research Digest Agent (arXiv streaming + LLM synthesis)
- **Project 11**: Tic Tac Toe with minimax AI

### 🖼️ Image Generation
- **Gemini image generation** on demand
- **User-scoped storage** with unique file paths

## Architecture

### Backend Structure
```
backend/app/
├── api/             # Route handlers (no business logic)
├── services/        # Business logic (testable, framework-agnostic)
├── models/          # SQLAlchemy ORM definitions
├── schemas/         # Pydantic request/response models
├── ai/              # LiteLLM client, chains, RAG, prompts
├── core/            # Config, security, logging
└── db/              # Session management, Alembic migrations
```

### Key Technologies
| Layer | Technology | Purpose |
|-------|-----------|----------|
| Frontend | React 18, TypeScript, Vite, Tailwind | UI, streaming render, dark mode |
| Backend | FastAPI, SQLAlchemy 2.0, Alembic | REST, ORM, migrations |
| Auth | JWT, bcrypt, Google OAuth 2.0 | Secure session, account linking |
| AI | LangChain LCEL, LiteLLM | Chain composition, LLM gateway |
| Vector | ChromaDB | Per-user RAG collections |
| Database | PostgreSQL + asyncpg | Production persistence |

## Environment Variables

Create `.env` in repo root:

```bash
# App
SECRET_KEY=your_secret_key_min_32_chars
JWT_EXPIRE_MINUTES=480
APP_NAME=amzur-ai-chat
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname

# LiteLLM Proxy (internal — VPN required)
LITELLM_PROXY_URL=https://litellm.amzur.com
LITELLM_API_KEY=sk-...
LLM_MODEL=gemini/gemini-2.5-flash
LITELLM_EMBEDDING_MODEL=text-embedding-3-large
IMAGE_GEN_MODEL=gemini/imagen-4.0-fast-generate-001

# Google OAuth (optional for testing)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# File & Vector Storage
MAX_UPLOAD_MB=20
UPLOAD_DIR=./uploads
CHROMA_PERSIST_DIR=./chroma_db
CHAT_MEMORY_CONVERSATION_LIMIT=5
```

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
