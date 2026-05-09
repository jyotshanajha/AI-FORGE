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
