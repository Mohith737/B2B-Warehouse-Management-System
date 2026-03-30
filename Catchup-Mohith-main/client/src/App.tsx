// client/src/App.tsx
import { RouterProvider } from 'react-router-dom'

import { AppProviders } from './providers'
import { appRouter } from './routes'

export default function App(): JSX.Element {
  return (
    <AppProviders>
      <RouterProvider router={appRouter} />
    </AppProviders>
  )
}
