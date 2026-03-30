// client/tests/utils/renderWithProviders.tsx
import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter } from 'react-router-dom'

import { AuthProvider } from '../../src/providers/AuthProvider'
import { ReactQueryProvider } from '../../src/providers/ReactQueryProvider'

type RenderWithProvidersOptions = {
  initialEntries?: string[]
}

export function renderWithProviders(
  ui: ReactElement,
  options: RenderWithProvidersOptions = {},
) {
  const { initialEntries = ['/'] } = options

  return render(
    <ReactQueryProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
      </AuthProvider>
    </ReactQueryProvider>,
  )
}
