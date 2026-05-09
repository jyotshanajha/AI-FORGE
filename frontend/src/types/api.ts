export type Role = 'user' | 'assistant'

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

export interface ChatAttachment {
  id: string
  filename: string
  mime_type: string
  size_bytes: number
  attachment_type: string
  download_url: string
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
