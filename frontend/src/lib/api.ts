import { z } from 'zod'

import type { AuthResponse, ChatTokenEvent, Message, Thread } from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

const authResponseSchema = z.object({
  user: z.object({
    id: z.string(),
    email: z.string().email(),
    created_at: z.string(),
  }),
})

const threadSchema = z.object({
  id: z.string(),
  title: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
})

const messageSchema = z.object({
  id: z.string(),
  thread_id: z.string(),
  role: z.enum(['user', 'assistant']),
  content: z.string(),
  created_at: z.string(),
})

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
  })

  if (!response.ok) {
    let errorMessage = `Request failed (${response.status})`
    try {
      const data = await response.json()
      if (data.detail) {
        if (typeof data.detail === 'string') {
          errorMessage = data.detail
        } else if (data.detail.message) {
          errorMessage = data.detail.message
        } else if (data.detail.error) {
          errorMessage = data.detail.error
        }
      }
    } catch {
      // If response is not JSON, use the status text
      errorMessage = response.statusText || errorMessage
    }
    throw new Error(errorMessage)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export async function register(email: string, password: string): Promise<AuthResponse> {
  const payload = await request<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  return authResponseSchema.parse(payload)
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const payload = await request<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  return authResponseSchema.parse(payload)
}

export async function logout(): Promise<void> {
  await request('/auth/logout', { method: 'POST' })
}

export async function me(): Promise<AuthResponse> {
  const payload = await request<AuthResponse>('/auth/me')
  return authResponseSchema.parse(payload)
}

export async function getGoogleLoginUrl(): Promise<string> {
  const payload = await request<{ url: string; state: string }>('/auth/google/login')
  return payload.url
}

export async function listThreads(): Promise<Thread[]> {
  const payload = await request<Thread[]>('/threads')
  return z.array(threadSchema).parse(payload)
}

export async function createThread(): Promise<Thread> {
  const payload = await request<Thread>('/threads', { method: 'POST', body: JSON.stringify({}) })
  return threadSchema.parse(payload)
}

export async function renameThread(threadId: string, title: string): Promise<Thread> {
  const payload = await request<Thread>(`/threads/${threadId}`, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  })
  return threadSchema.parse(payload)
}

export async function deleteThread(threadId: string): Promise<void> {
  await request(`/threads/${threadId}`, { method: 'DELETE' })
}

export async function listMessages(threadId: string): Promise<Message[]> {
  const payload = await request<Message[]>(`/chat/${threadId}/messages`)
  return z.array(messageSchema).parse(payload)
}

export async function streamChat(
  threadId: string,
  message: string,
  onToken: (event: ChatTokenEvent) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ thread_id: threadId, message }),
  })

  if (!response.ok || !response.body) {
    throw new Error(`Stream failed (${response.status})`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() ?? ''

    for (const rawEvent of events) {
      if (!rawEvent.startsWith('data: ')) {
        continue
      }
      const data = rawEvent.slice('data: '.length)
      if (data === '[DONE]') {
        return
      }
      const parsed = JSON.parse(data) as ChatTokenEvent
      onToken(parsed)
    }
  }
}
