import { z } from 'zod'

import type { AuthResponse, ChatAttachment, ChatTokenEvent, Message, Thread } from '../types/api'

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

const attachmentSchema = z.object({
  id: z.string(),
  filename: z.string(),
  mime_type: z.string(),
  size_bytes: z.number(),
  attachment_type: z.string(),
  download_url: z.string(),
})

const messageSchema = z.object({
  id: z.string(),
  thread_id: z.string(),
  role: z.enum(['user', 'assistant']),
  content: z.string(),
  created_at: z.string(),
  attachments: z.array(attachmentSchema).default([]),
})

const imageGenerationResponseSchema = z.object({
  url: z.string(),
  filename: z.string(),
  mime_type: z.string(),
  original_prompt: z.string(),
  size_bytes: z.number(),
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

function toAbsoluteDownloadUrl(downloadUrl: string): string {
  if (downloadUrl.startsWith('http://') || downloadUrl.startsWith('https://')) {
    return downloadUrl
  }
  return `${API_BASE_URL}${downloadUrl}`
}

function normalizeAttachment(attachment: ChatAttachment): ChatAttachment {
  return {
    ...attachment,
    download_url: toAbsoluteDownloadUrl(attachment.download_url),
  }
}

export async function uploadAttachment(file: File): Promise<ChatAttachment> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/chat/attachments`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
  })

  if (!response.ok) {
    let errorMessage = `Upload failed (${response.status})`
    try {
      const data = await response.json()
      if (data?.detail?.message) {
        errorMessage = data.detail.message
      }
    } catch {
      errorMessage = response.statusText || errorMessage
    }
    throw new Error(errorMessage)
  }

  const payload = attachmentSchema.parse(await response.json())
  return normalizeAttachment(payload)
}

export async function listMessages(threadId: string): Promise<Message[]> {
  const payload = await request<Message[]>(`/chat/${threadId}/messages`)
  return z.array(messageSchema).parse(payload).map((message) => ({
    ...message,
    attachments: message.attachments.map(normalizeAttachment),
  }))
}

export async function streamChat(
  threadId: string,
  message: string,
  onToken: (event: ChatTokenEvent) => void,
  attachmentIds: string[] = [],
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ thread_id: threadId, message, attachment_ids: attachmentIds }),
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

export async function generateImage(prompt: string, threadId?: string): Promise<ChatAttachment> {
  const payload = await request<any>('/chat/generate-image', {
    method: 'POST',
    body: JSON.stringify({ prompt, thread_id: threadId }),
  })

  // Convert image response to attachment format
  const response = imageGenerationResponseSchema.parse(payload)
  return {
    id: crypto.randomUUID(),
    filename: response.filename,
    mime_type: response.mime_type,
    size_bytes: response.size_bytes,
    attachment_type: 'image',
    download_url: response.url,
  }
}
