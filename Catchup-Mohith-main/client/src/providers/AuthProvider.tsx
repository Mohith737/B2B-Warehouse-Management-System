// client/src/providers/AuthProvider.tsx
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { useAuthStore } from '../stores/authStore'

type AuthContextValue = {
  initialized: boolean
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

type AuthProviderProps = {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps): JSX.Element {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const [initialized, setInitialized] = useState(false)

  useEffect(() => {
    setInitialized(true)
  }, [])

  const value = useMemo(
    () => ({
      initialized,
      isAuthenticated,
    }),
    [initialized, isAuthenticated],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

function useAuthContext(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    return {
      initialized: true,
      isAuthenticated: false,
    }
  }
  return context
}

void useAuthContext
