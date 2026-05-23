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

export type ResearchDigestTokenEvent =
  | { type: 'token'; token: string }
  | { type: 'status'; message: string }
  | {
      type: 'meta'
      query: string
      papers_found: number
      rounds_executed?: number
      query_variants?: string[]
    }
  | {
      type: 'evidence_decision'
      enough_evidence: boolean
      confidence: number
      reason: string
      papers_considered: number
    }
  | {
      type: 'sources'
      papers: Array<{
        title: string
        id: string
        published: string
        authors: string[]
      }>
    }
  | { type: 'error'; message: string }

export interface DataframeQueryResponse {
  answer: string
  source_type: string
  source_name: string
  row_count: number
  column_count: number
  columns: string[]
  generated_code?: string | null
  intermediate_steps: string[]
}

export interface TicTacToeMoveResponse {
  board: string[]
  ai_move?: number
  winner?: string
  status: 'in_progress' | 'finished' | 'draw'
  next_turn?: string
}
