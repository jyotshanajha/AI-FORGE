export type Role = 'user' | 'assistant'
export type ChatResponseMode = 'rag' | 'llm' | 'sql'

export interface User {
  id: string
  email: string
  created_at: string
}

export interface AuthResponse {
  user: User
}

export interface Thread {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export interface RagInfo {
  chunks_count: number
  page_count: number
  characters_processed: number
}

export interface ChatAttachment {
  id: string
  filename: string
  mime_type: string
  size_bytes: number
  attachment_type: string
  download_url: string
  rag_info?: RagInfo
}

export interface Message {
  id: string
  thread_id: string
  role: Role
  content: string
  created_at: string
  attachments: ChatAttachment[]
}

export interface ChatTokenEvent {
  token: string
}

export interface ResearchDigestTokenEvent {
  token: string
}

export interface TicTacToeMoveResponse {
  board: string[]
  ai_move?: number
  winner?: string
  status: 'in_progress' | 'finished' | 'draw'
  next_turn?: string
}
