import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LanguageProvider } from './i18n/LanguageContext'
import App from './App'
import './index.css'

// Case artifacts are persisted by the backend. Keep them fresh enough for
// normal edits while avoiding repeated navigation-only requests.
const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 60_000, retry: 1 } } })

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}><LanguageProvider><App /></LanguageProvider></QueryClientProvider>
  </StrictMode>,
)

