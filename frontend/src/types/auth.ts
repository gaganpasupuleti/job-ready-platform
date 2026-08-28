export interface User {
  id: string
  email: string
  username: string
  full_name: string | null
  role: 'student' | 'admin' | 'trainer'
  is_active: boolean
  created_at: string
}

export interface AuthResponse {
  user: User
  access_token: string
  token_type: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  username: string
  full_name?: string
  password: string
}
