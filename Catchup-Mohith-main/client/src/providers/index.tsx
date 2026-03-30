// client/src/providers/index.tsx
import type { ReactNode } from 'react'

import { AuthProvider } from './AuthProvider'
import { ReactQueryProvider } from './ReactQueryProvider'

type AppProvidersProps = {
  children: ReactNode
}

export function AppProviders({ children }: AppProvidersProps): JSX.Element {
  return (
    <ReactQueryProvider>
      <AuthProvider>{children}</AuthProvider>
    </ReactQueryProvider>
  )
}
