# Frontend — React 18 + TypeScript + Tailwind

**Status**: ✅ Production-ready  
**Framework**: React 18 + TypeScript + Vite  
**Styling**: Tailwind CSS 3  
**State**: React Query + Zustand  

---

## Quick Start

```bash
npm install
npm run dev   # Start dev server at http://localhost:5173
npm run build # Production build
```

## Project Structure

```
src/
├── pages/
│   ├── LoginPage.tsx          # Auth + OAuth
│   └── ChatPage.tsx           # Main chat interface
├── components/
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   └── GoogleLoginButton.tsx
│   ├── chat/
│   │   ├── MessageList.tsx
│   │   ├── InputBar.tsx
│   │   └── ThreadSidebar.tsx
│   ├── agents/
│   │   ├── ResearchDigestPanel.tsx
│   │   └── TicTacToePanel.tsx
│   └── attachments/
│       └── AttachmentUpload.tsx
├── hooks/
│   ├── useAuth.ts
│   ├── useChat.ts
│   └── useThreadList.ts
├── lib/
│   ├── api.ts       # HTTP client (all requests here)
│   ├── auth.ts      # JWT/cookie helpers
│   └── utils.ts     # Utilities
├── types/
│   └── api.ts       # Shared TypeScript interfaces
└── index.css        # Tailwind directives
```

## Key Features

✅ **Authentication**
- Email/password registration & login
- Google OAuth 2.0
- Session persistence via httpOnly cookies

✅ **Chat Interface**
- Real-time token streaming (SSE)
- Thread-based conversations
- Auto-scroll to latest message
- Markdown + code + LaTeX rendering

✅ **Response Modes**
- **LLM**: Standard chat
- **SQL**: NL queries → SQL execution
- **Image**: Text → image generation
- **Research**: arXiv digest synthesis
- **Game**: Tic Tac Toe with AI

✅ **Attachments**
- Image upload (JPG, PNG, WebP)
- PDF for RAG
- CSV/Excel for analysis

✅ **UI/UX**
- Dark mode support
- Responsive layout
- Loading states
- Error boundaries

## Development

```bash
npm run lint    # ESLint + Prettier
npm run type-check  # TypeScript check
npm run build   # Production build
```
