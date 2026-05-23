import { z } from 'zod'

import type {
  AuthResponse,
  ChatAttachment,
  ChatResponseMode,
  ChatTokenEvent,
  DataframeQueryResponse,
  Message,
  ResearchDigestTokenEvent,
  Thread,
  TicTacToeMoveResponse,
} from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'
const DEFAULT_REQUEST_TIMEOUT_MS = 30000

interface RequestOptions extends RequestInit {
  timeoutMs?: number
}

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

const ragInfoSchema = z.object({
  chunks_count: z.number(),
  page_count: z.number(),
  characters_processed: z.number(),
})

const ragInfoOptionalSchema = z.preprocess(
  (value) => (value === null ? undefined : value),
  ragInfoSchema.optional(),
)

const attachmentSchema = z.object({
  id: z.string(),
  filename: z.string(),
  mime_type: z.string(),
  size_bytes: z.number(),
  attachment_type: z.string(),
  download_url: z.string(),
  rag_info: ragInfoOptionalSchema,
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
  attachment: attachmentSchema,
  original_prompt: z.string(),
  message_id: z.string().optional().nullable(),
})

const dataframeQueryResponseSchema = z.object({
  answer: z.string(),
  source_type: z.string(),
  source_name: z.string(),
  row_count: z.number(),
  column_count: z.number(),
  columns: z.array(z.string()),
  generated_code: z.string().nullable().optional(),
  intermediate_steps: z.array(z.string()).default([]),
})

export interface GeneratedImageResult {
  attachment: ChatAttachment
  messageId?: string
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { timeoutMs = DEFAULT_REQUEST_TIMEOUT_MS, ...fetchOptions } = options
  const controller = new AbortController()
  const timeout = setTimeout(() => {
    controller.abort(new DOMException('Request timed out', 'TimeoutError'))
  }, timeoutMs)

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...fetchOptions,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(fetchOptions.headers ?? {}),
      },
      signal: controller.signal,
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
  } catch (error) {
    if (controller.signal.aborted) {
      const reason = controller.signal.reason
      if (reason instanceof DOMException && reason.name === 'TimeoutError') {
        throw new Error(`Request timed out after ${Math.round(timeoutMs / 1000)}s. Please try again.`)
      }
      throw new Error('Request was cancelled. Please retry.')
    }

    if (error instanceof Error) {
      throw error
    }
    throw new Error('Network request failed')
  } finally {
    clearTimeout(timeout)
  }
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
    rag_info: attachment.rag_info ?? undefined,
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
  responseMode: ChatResponseMode = 'rag',
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      thread_id: threadId,
      message,
      attachment_ids: attachmentIds,
      response_mode: responseMode,
    }),
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

export async function generateImage(prompt: string, threadId?: string): Promise<GeneratedImageResult> {
  const payload = await request<any>('/chat/generate-image', {
    method: 'POST',
    body: JSON.stringify({ prompt, thread_id: threadId }),
  })

  const response = imageGenerationResponseSchema.parse(payload)
  return {
    attachment: normalizeAttachment(response.attachment),
    messageId: response.message_id ?? undefined,
  }
}

export async function streamResearchDigest(
  query: string,
  onToken: (event: ResearchDigestTokenEvent) => void,
  options: {
    maxPapers?: number
    maxRounds?: number
    papersPerRound?: number
    signal?: AbortSignal
  } = {},
): Promise<void> {
  const { maxPapers = 6, maxRounds = 3, papersPerRound = 5, signal } = options
  const response = await fetch(`${API_BASE_URL}/agents/research-digest/stream`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      max_papers: maxPapers,
      max_rounds: maxRounds,
      papers_per_round: papersPerRound,
    }),
    signal,
  })

  if (!response.ok || !response.body) {
    throw new Error(`Research stream failed (${response.status})`)
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
      const parsed = JSON.parse(data) as Record<string, unknown>

      if (typeof parsed.type === 'string') {
        onToken(parsed as ResearchDigestTokenEvent)
        continue
      }

      // Backward compatibility with token-only payloads.
      if (typeof parsed.token === 'string') {
        onToken({ type: 'token', token: parsed.token })
      }
    }
  }
}

export async function dataframeQuery(input: {
  question: string
  attachmentId?: string
  googleSheetId?: string
  worksheetName?: string
}): Promise<DataframeQueryResponse> {
  const payload = await request<DataframeQueryResponse>('/agents/dataframe-query', {
    method: 'POST',
    timeoutMs: 120000,
    body: JSON.stringify({
      question: input.question,
      attachment_id: input.attachmentId,
      google_sheet_id: input.googleSheetId,
      worksheet_name: input.worksheetName,
    }),
  })
  return dataframeQueryResponseSchema.parse(payload)
}

export async function ticTacToeMove(board: string[], playerMove: number): Promise<TicTacToeMoveResponse> {
  return request<TicTacToeMoveResponse>('/agents/tic-tac-toe/move', {
    method: 'POST',
    body: JSON.stringify({ board, player_move: playerMove }),
  })
}
