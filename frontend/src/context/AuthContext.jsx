import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, onSessionChange, refreshSession, setAccessToken } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // 'loading' until we know whether the refresh cookie gives us a session
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    onSessionChange(setUser)
    refreshSession()
      .catch(() => setUser(null))
      .finally(() => setStatus('ready'))
  }, [])

  /** Save the result of login, email verification or invitation acceptance. */
  const startSession = useCallback((authResponse) => {
    setAccessToken(authResponse.access_token)
    setUser(authResponse.user)
  }, [])

  const login = useCallback(
    async (email, password) => {
      const data = await api.post('/api/auth/login', { email, password })
      startSession(data)
      return data.user
    },
    [startSession],
  )

  const logout = useCallback(async () => {
    try {
      await api.post('/api/auth/logout')
    } finally {
      setAccessToken(null)
      setUser(null)
    }
  }, [])

  const refreshUser = useCallback(async () => {
    const me = await api.get('/api/auth/me')
    setUser(me)
    return me
  }, [])

  const value = useMemo(
    () => ({ user, status, login, logout, startSession, refreshUser }),
    [user, status, login, logout, startSession, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext)
}
