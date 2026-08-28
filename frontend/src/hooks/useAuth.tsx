import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { getAuthToken } from '@/api/client'
import { fetchMe, login, logoutApi, register } from '@/services/authService'
import type { AuthResponse, LoginPayload, RegisterPayload, User } from '@/types/auth'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (payload: LoginPayload) => Promise<AuthResponse>
  register: (payload: RegisterPayload) => Promise<AuthResponse>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const token = getAuthToken()
    if (!token) {
      setUser(null)
      return
    }
    const me = await fetchMe()
    setUser(me)
  }, [])

  useEffect(() => {
    refreshUser()
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false))
  }, [refreshUser])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
      login: async (payload) => {
        const response = await login(payload)
        setUser(response.user)
        return response
      },
      register: async (payload) => {
        const response = await register(payload)
        setUser(response.user)
        return response
      },
      logout: async () => {
        await logoutApi()
        setUser(null)
      },
      refreshUser,
    }),
    [user, isLoading, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
