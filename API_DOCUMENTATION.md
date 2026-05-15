# API Documentation — Amzur AI Chat

**Base URL**: `http://localhost:8000/api`  
**Format**: JSON  
**Auth**: JWT in httpOnly cookies + `user_email` metadata on AI calls  
**Rate Limits**: Per-user quota enforced via LiteLLM

---

## 🔐 Authentication

### Register
```
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response 200:
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com"
  }
}
```

### Login
```
POST /auth/login

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response 200:
{
  "user": {"id": "...", "email": "..."}
}  
Set-Cookie: access_token=jwt_token; HttpOnly; Secure; SameSite=Lax
```

### Get Current User
```
GET /auth/me
Cookie: access_token=...

Response 200:
{
  "user": {"id": "...", "email": "user@example.com"}
}
```

### Logout
```
POST /auth/logout
Cookie: access_token=...

Response 200
Set-Cookie: access_token=; Max-Age=0; HttpOnly
```

### Google OAuth
```
GET /auth/google/login
→ Redirects to Google consent screen

GET /auth/google/callback?code=...
→ Exchanges code, creates/links user, redirects to frontend
→ Sets access_token cookie
```

---

## 💬 Chat & Streaming

### Send Message (Stream)
```
POST /chat/stream
Cookie: access_token=...

{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "What are neural networks?",
  "attachment_ids": [],
  "response_mode": "llm"
}

Response 200 (text/event-stream):
data: {"token": "Neural"}
data: {"token": " networks"}
data: {"token": " are..."}
...
data: [DONE]
```

### Generate Image
```
POST /chat/generate-image
Cookie: access_token=...

{
  "thread_id": "...",
  "prompt": "A serene mountain landscape at sunset"
}

Response 200:
{
  "image_url": "http://localhost:8000/uploads/d289411a.../image.jpg"
}
```

### Get Messages
```
GET /chat/{thread_id}/messages
Cookie: access_token=...

Response 200:
{
  "messages": [
    {
      "id": "...",
      "thread_id": "...",
      "content": "Hello",
      "role": "user",
      "created_at": "2026-05-15T10:30:00+00:00"
    },
    ...
  ]
}
```

### Upload File
```
POST /chat/upload
Cookie: access_token=...
Content-Type: multipart/form-data

file: <binary file data>

Response 200:
{
  "attachment_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "README.md",
  "mimetype": "text/markdown",
  "size": 1024
}
```

---

## 🧵 Threads

### Create Thread
```
POST /threads/create
Cookie: access_token=...

Response 201:
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Untitled",
  "created_at": "2026-05-15T10:30:00+00:00"
}
```

### List Threads
```
GET /threads
Cookie: access_token=...

Response 200:
{
  "threads": [
    {
      "id": "...",
      "title": "Project Discussion",
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
```

### Rename Thread
```
PUT /threads/{thread_id}/rename
Cookie: access_token=...

{
  "new_title": "ML Research"
}

Response 200:
{
  "thread_id": "...",
  "title": "ML Research"
}
```

### Delete Thread
```
DELETE /threads/{thread_id}
Cookie: access_token=...

Response 204 (No Content)
```

---

## 🤖 Agents

### Research Digest (Stream)
```
POST /agents/research-digest/stream
Cookie: access_token=...

{
  "query": "machine learning interpretability",
  "max_papers": 5
}

Response 200 (text/event-stream):
data: {"token": "## Research"}
data: {"token": " Digest:"}
...
data: [DONE]
```

### Tic Tac Toe Move
```
POST /agents/tic-tac-toe/move
Cookie: access_token=...

{
  "board": [0, 0, 0, 0, 0, 0, 0, 0, 0],
  "player_move": 4
}

Response 200:
{
  "board": [0, 0, 0, 0, 1, 0, 0, 0, 0],
  "ai_move": 0,
  "winner": null,
  "status": "in_progress",
  "next_turn": "player"
}
```

---

## 📊 SQL Queries (Natural Language)

### Chat with SQL Mode
```
POST /chat/stream
Cookie: access_token=...

{
  "thread_id": "...",
  "message": "How many active users do we have?",
  "response_mode": "sql"
}

Response 200 (text/event-stream):
data: {"token": "| user_id"}
data: {"token": " | count"}
...
data: [DONE]
```

**Safety Features:**
- Case-insensitive keyword block: INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER
- Read-only execution only
- Schema introspection via `information_schema`
- User-scoped query results

---

## ✅ Health Check

```
GET /health

Response 200:
{
  "status": "ok"
}
```
```

**Response** (200)
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2026-05-09T10:30:00+00:00"
  }
}
```

**Side Effect**: Sets `access_token` cookie (httpOnly, SameSite=lax)

**Errors**
- `401`: Invalid credentials
- `404`: User not found

---

### 3. Get Google OAuth URL
**GET** `/auth/google/login`

**Query Parameters**: None

**Response** (200)
```json
{
  "url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&state=...",
  "state": "state-550e8400-e29b-41d4-a716-446655440000-1778309996"
}
```

**Usage**: Redirect browser to the returned `url`

---

### 4. Google OAuth Callback
**GET** `/auth/google/callback`

**Query Parameters**
- `code` (required): Authorization code from Google
- `state` (optional): State parameter for CSRF protection

**Response** (302 Redirect)
Redirects to `http://localhost:5173` with `access_token` cookie set

**Side Effects**:
- Creates user if new Google email
- Links Google account if email exists
- Sets JWT `access_token` cookie

**Error Response** (302 Redirect)
Redirects to `http://localhost:5173?error=google_auth_failed&message=Error%20description`

---

### 5. Get Current User
**GET** `/auth/me`

**Headers**
```
Authorization: (Cookie: access_token=...)
```

**Response** (200)
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2026-05-09T10:30:00+00:00"
  }
}
```

**Errors**
- `401`: Not authenticated
- `500`: Database error

---

### 6. Logout
**POST** `/auth/logout`

**Request Body**: Empty

**Response** (200)
```json
{
  "status": "ok"
}
```

**Side Effect**: Deletes `access_token` cookie

---

## Thread Management Endpoints

### 1. List All User Threads
**GET** `/threads`

**Query Parameters**: None

**Response** (200)
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "title": "My First Chat",
    "created_at": "2026-05-09T10:30:00+00:00",
    "updated_at": "2026-05-09T10:30:00+00:00"
  },
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "title": "New Chat",
    "created_at": "2026-05-08T15:20:00+00:00",
    "updated_at": "2026-05-08T15:20:00+00:00"
  }
]
```

**Errors**
- `401`: Not authenticated

---

### 2. Create New Thread
**POST** `/threads`

**Request Body**
```json
{
  "title": "My Project Discussion"
}
```
(Optional: if omitted, defaults to "New Chat")

**Response** (201)
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "title": "My Project Discussion",
  "created_at": "2026-05-09T10:30:00+00:00",
  "updated_at": "2026-05-09T10:30:00+00:00"
}
```

**Errors**
- `401`: Not authenticated
- `400`: Invalid title format

---

### 3. Rename Thread
**PATCH** `/threads/{thread_id}`

**Path Parameters**
- `thread_id`: UUID of thread to rename

**Request Body**
```json
{
  "title": "Updated Thread Title"
}
```

**Response** (200)
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "title": "Updated Thread Title",
  "created_at": "2026-05-09T10:30:00+00:00",
  "updated_at": "2026-05-09T10:35:00+00:00"
}
```

**Errors**
- `401`: Not authenticated
- `404`: Thread not found or doesn't belong to user
- `400`: Invalid title format

---

### 4. Delete Thread
**DELETE** `/threads/{thread_id}`

**Path Parameters**
- `thread_id`: UUID of thread to delete

**Response** (204)
No content

**Side Effect**: Cascades delete to all messages in thread

**Errors**
- `401`: Not authenticated
- `404`: Thread not found or doesn't belong to user

---

## Chat & Message Endpoints

### 1. Get Thread Messages
**GET** `/chat/{thread_id}/messages`

**Path Parameters**
- `thread_id`: UUID of thread

**Query Parameters**: None

**Response** (200)
```json
[
  {
    "id": "990e8400-e29b-41d4-a716-446655440000",
    "thread_id": "660e8400-e29b-41d4-a716-446655440000",
    "role": "user",
    "content": "What is the weather?",
    "created_at": "2026-05-09T10:30:00+00:00"
  },
  {
    "id": "aa0e8400-e29b-41d4-a716-446655440000",
    "thread_id": "660e8400-e29b-41d4-a716-446655440000",
    "role": "assistant",
    "content": "I don't have access to real-time weather data...",
    "created_at": "2026-05-09T10:30:05+00:00"
  }
]
```

**Errors**
- `401`: Not authenticated
- `404`: Thread not found or doesn't belong to user

---

### 2. Stream Chat Response
**POST** `/chat/stream`

**Request Body**
```json
{
  "thread_id": "660e8400-e29b-41d4-a716-446655440000",
  "message": "What can you help me with?"
}
```

**Response** (200 - Server-Sent Events)
```
data: {"token":"Hello"}
data: {"token":" there"}
data: {"token":"."}
data: [DONE]
```

**Process Flow**
1. User message is saved to DB immediately
2. Message history is retrieved from DB
3. LLM is called with history and new message
4. Response is streamed back token-by-token
5. Complete response is saved to DB
6. Thread title is auto-generated if first message

**Response Headers**
- `Content-Type: text/event-stream`
- `Transfer-Encoding: chunked`

**Errors**
- `401`: Not authenticated
- `404`: Thread not found or doesn't belong to user
- `502`: LLM error (when LiteLLM unavailable)

**Frontend Implementation**
```javascript
const response = await fetch('http://localhost:8000/api/chat/stream', {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ thread_id, message })
})

const reader = response.body.getReader()
const decoder = new TextDecoder()

while (true) {
  const { done, value } = await reader.read()
  if (done) break
  
  const chunk = decoder.decode(value)
  const lines = chunk.split('\n')
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6))
      if (data.token) {
        // Append token to message
      }
    }
  }
}
```

---

## Error Response Format

All error responses follow this format:

**Status Code**: 4xx or 5xx

**Response Body**
```json
{
  "detail": {
    "error": "error_code",
    "message": "Human-readable error message"
  }
}
```

**Common Error Codes**
- `not_authenticated`: JWT missing or invalid
- `not_found`: Resource doesn't exist
- `access_denied`: User lacks permission
- `invalid_input`: Request validation failed
- `database_error`: Database operation failed
- `llm_error`: AI service error
- `google_not_configured`: OAuth credentials missing

---

## Request Examples

### Example 1: Complete Login Flow
```bash
# 1. Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'

# 2. Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}' \
  -c cookies.txt

# 3. Get current user
curl -X GET http://localhost:8000/api/auth/me \
  -b cookies.txt
```

### Example 2: Thread & Message Flow
```bash
# 1. Create thread
curl -X POST http://localhost:8000/api/threads \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"title":"My Chat"}' \
  | jq .id > thread_id.txt

# 2. Send message (stream)
THREAD_ID=$(cat thread_id.txt)
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d "{\"thread_id\":\"$THREAD_ID\",\"message\":\"Hello!\"}"

# 3. Get messages
curl -X GET "http://localhost:8000/api/chat/$THREAD_ID/messages" \
  -b cookies.txt | jq .
```

### Example 3: Google OAuth Flow
```bash
# 1. Get OAuth URL
curl http://localhost:8000/api/auth/google/login | jq .url

# 2. Visit that URL in browser
# User completes Google authentication and browser is redirected to:
# http://localhost:5173?code=...&state=...

# 3. Backend automatically handles callback at:
# http://localhost:8000/api/auth/google/callback?code=...&state=...

# 4. User is redirected to http://localhost:5173 with JWT cookie set
```

---

## Authentication & Authorization

### JWT Structure
```
Header: { "alg": "HS256", "typ": "JWT" }
Payload: {
  "sub": "user-uuid",
  "email": "user@example.com",
  "exp": 1778395596
}
```

### Cookie Settings
```
Set-Cookie: access_token=<JWT>; HttpOnly; SameSite=Lax; Path=/; Max-Age=28800
```

### Session Duration
- Default: 480 minutes (8 hours)
- Configurable via `JWT_EXPIRE_MINUTES` in `.env`

### Refresh Token
Not implemented. Users must re-authenticate after JWT expiration.

---

## Rate Limiting
Not currently implemented. Consider adding for production.

---

## API Versioning
Currently on v1 (implicit). All endpoints at `/api/`

Future versions would use `/api/v2/`, etc.

---

## Pagination
Not implemented for list endpoints. Consider adding for large datasets.

---

## Webhooks
Not implemented.

---

## WebSocket Support
Not implemented. Using Server-Sent Events (SSE) for streaming instead.

---

## CORS Configuration
```
Allow-Origin: http://localhost:5173
Allow-Credentials: true
Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
Allow-Headers: Content-Type, Authorization
```

---

## Data Types

### UUID
Format: `550e8400-e29b-41d4-a716-446655440000`

### DateTime
Format: `2026-05-09T10:30:00+00:00` (ISO 8601 with timezone)

### Role Enum
Values: `user` | `assistant`

---

## Testing the API

### Using curl
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test auth endpoint
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!"}'
```

### Using Postman
1. Import from Swagger: `http://localhost:8000/openapi.json`
2. Set Base URL: `http://localhost:8000/api`
3. Create requests for each endpoint

### Using Python Requests
```python
import requests

BASE_URL = 'http://localhost:8000/api'
session = requests.Session()

# Register
session.post(f'{BASE_URL}/auth/register', json={
    'email': 'test@test.com',
    'password': 'Test123!'
})

# Login
session.post(f'{BASE_URL}/auth/login', json={
    'email': 'test@test.com',
    'password': 'Test123!'
})

# Get threads
threads = session.get(f'{BASE_URL}/threads').json()
print(threads)
```

---

## Changelog

### Version 1.0 (Current)
- ✅ Email/password authentication
- ✅ Google OAuth 2.0
- ✅ Thread management (CRUD)
- ✅ Message persistence
- ✅ Chat streaming
- ✅ Thread auto-titling

---

