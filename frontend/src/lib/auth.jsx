import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { USER_KEY, authApi, clearTokens, getAccessToken, setTokens } from './api'
import { can as canHelper } from '../utils/constants'

const AuthContext = createContext(null)

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    setUser(readStoredUser())
    setReady(true)
    const onLogout = () => setUser(null)
    window.addEventListener('ab:logout', onLogout)
    return () => window.removeEventListener('ab:logout', onLogout)
  }, [])

  const applySession = useCallback((data) => {
    setTokens(data.access_token, data.refresh_token)
    localStorage.setItem(USER_KEY, JSON.stringify(data.user))
    setUser(data.user)
  }, [])

  const login = useCallback(
    async (email, password) => {
      const { data } = await authApi.post('/api/auth/login', { email, password })
      applySession(data)
      return data.user
    },
    [applySession],
  )

  const register = useCallback(
    async (payload) => {
      const { data } = await authApi.post('/api/auth/register', payload)
      applySession(data)
      return data.user
    },
    [applySession],
  )

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem('ab_refresh_token')
    try {
      await authApi.post('/api/auth/logout', { refresh_token: refresh })
    } catch {
      /* best-effort revocation */
    } finally {
      clearTokens()
      setUser(null)
    }
  }, [])

  const refreshMe = useCallback(async () => {
    if (!getAccessToken()) return
    try {
      const { data } = await authApi.get('/api/auth/me')
      localStorage.setItem(USER_KEY, JSON.stringify(data.user))
      setUser(data.user)
    } catch {
      /* interceptor handles 401 */
    }
  }, [])

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      ready,
      login,
      register,
      logout,
      refreshMe,
      can: (permission) => canHelper(user?.role, permission),
      hasRole: (role) => user?.role === role,
    }),
    [user, ready, login, register, logout, refreshMe],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}