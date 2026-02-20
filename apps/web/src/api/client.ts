import { useAuthStore } from '@/stores/authStore'
import type { User, CreateUserData, UpdateUserData } from '@/types'

const API_BASE = '/api/v1'

interface RequestOptions extends RequestInit {
  skipAuth?: boolean
}

class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown
  ) {
    super(`API Error: ${status} ${statusText}`)
    this.name = 'ApiError'
  }
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { skipAuth = false, ...fetchOptions } = options
  const url = `${API_BASE}${endpoint}`

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(fetchOptions.headers as Record<string, string>),
  }

  // Add auth header if authenticated
  if (!skipAuth) {
    const token = useAuthStore.getState().accessToken
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  const response = await fetch(url, {
    ...fetchOptions,
    headers,
  })

  if (!response.ok) {
    // Handle 401 - try refresh token
    if (response.status === 401 && !options.skipAuth) {
      const state = useAuthStore.getState()
      const refreshToken = state.refreshToken

      if (refreshToken) {
        try {
          // Attempt refresh
          const refreshResponse = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          })

          if (refreshResponse.ok) {
            const data = await refreshResponse.json()
            state.setTokens(data.access_token, refreshToken)

            // Retry original request with new token
            const retryHeaders = {
              ...headers,
              'Authorization': `Bearer ${data.access_token}`
            }
            const retryResponse = await fetch(url, {
              ...fetchOptions,
              headers: retryHeaders,
            })

            if (retryResponse.ok) {
              if (retryResponse.status === 204) return undefined as T
              return retryResponse.json()
            }
          }
        } catch (e) {
          console.error("Token refresh failed", e)
        }
      }

      // If refresh failed or no token, logout
      state.logout()
    }

    let errorData
    try {
      errorData = await response.json()
    } catch {
      // Response is not JSON
    }

    throw new ApiError(response.status, response.statusText, errorData)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),

  patch: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    }),

  put: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),

  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),

  // File upload
  upload: async <T>(
    endpoint: string,
    file: File,
    options: RequestOptions = {}
  ): Promise<T> => {
    const formData = new FormData()
    formData.append('file', file)

    const url = `${API_BASE}${endpoint}`
    const state = useAuthStore.getState()

    const getHeaders = () => {
      const h: Record<string, string> = {}
      if (!options.skipAuth) {
        const token = state.accessToken
        if (token) {
          h['Authorization'] = `Bearer ${token}`
        }
      }
      return h
    }

    let response = await fetch(url, {
      method: 'POST',
      headers: getHeaders(),
      body: formData,
    })

    if (!response.ok && response.status === 401 && !options.skipAuth) {
      const refreshToken = state.refreshToken
      if (refreshToken) {
        try {
          const refreshResponse = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          })

          if (refreshResponse.ok) {
            const data = await refreshResponse.json()
            state.setTokens(data.access_token, refreshToken)

            // Retry with new token
            response = await fetch(url, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${data.access_token}`
              },
              body: formData,
            })
          }
        } catch (e) {
          console.error("Upload token refresh failed", e)
        }
      }

      if (!response.ok && response.status === 401) {
        state.logout()
      }
    }

    if (!response.ok) {
      let errorData
      try {
        errorData = await response.json()
      } catch { }
      throw new ApiError(response.status, response.statusText, errorData)
    }

    return response.json()
  },

  // Users
  getUsers: async (): Promise<User[]> => {
    return request<User[]>('/users')
  },

  createUser: async (data: CreateUserData): Promise<User> => {
    return request<User>('/users', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  getUser: async (id: string): Promise<User> => {
    return request<User>(`/users/${id}`)
  },

  updateUser: async (id: string, data: UpdateUserData): Promise<User> => {
    return request<User>(`/users/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },

  deleteUser: async (id: string): Promise<void> => {
    return request<void>(`/users/${id}`, {
      method: 'DELETE',
    })
  },
}

export { ApiError }
