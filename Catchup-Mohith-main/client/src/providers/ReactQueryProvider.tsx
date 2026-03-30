// client/src/providers/ReactQueryProvider.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import type { ReactNode } from 'react'

type ReactQueryProviderProps = {
  children: ReactNode
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      refetchIntervalInBackground: false,
    },
    mutations: {
      retry: 0,
    },
  },
})

export function ReactQueryProvider({ children }: ReactQueryProviderProps): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {import.meta.env.DEV ? <ReactQueryDevtools initialIsOpen={false} /> : null}
    </QueryClientProvider>
  )
}
