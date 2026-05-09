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

export interface Message {
  id: string
  thread_id: string
  role: Role
  content: string
  created_at: string
}

export interface ChatTokenEvent {
  token: string
}
