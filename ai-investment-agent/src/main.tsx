import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import App from './App'
import { queryClient } from './lib/query-client'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1a2235',
            color: '#e2e8f0',
            border: '1px solid #243044',
            borderRadius: '8px',
          },
          success: { iconTheme: { primary: '#10b981', secondary: '#0a0e1a' } },
          error: { iconTheme: { primary: '#ef4444', secondary: '#0a0e1a' } },
        }}
      />
    </QueryClientProvider>
  </React.StrictMode>
)
