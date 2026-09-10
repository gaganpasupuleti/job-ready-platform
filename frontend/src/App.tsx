import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { AuthProvider } from '@/hooks/useAuth'
import { queryClient } from '@/queryClient'
import { AppRoutes } from '@/routes'

import './index.css'

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ErrorBoundary>
            <AppRoutes />
          </ErrorBoundary>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
