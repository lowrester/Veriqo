import { api } from './client'

interface LoginRequest {
  email: string
  password: string
}

interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

interface UserResponse {
  id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
}

export const authApi = {
  login: (data: LoginRequest) =>
    api.post<LoginResponse>('/auth/login', data, { skipAuth: true }),

  refresh: (refreshToken: string) =>
    api.post<{ access_token: string; token_type: string; expires_in: number }>(
      '/auth/refresh',
      { refresh_token: refreshToken },
      { skipAuth: true }
    ),

  me: () => api.get<UserResponse>('/auth/me'),
}
