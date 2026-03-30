// client/src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'

import './design-system/tokens/index.scss'
import App from './App'

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
