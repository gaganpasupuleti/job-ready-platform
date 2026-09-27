import { QueryClient } from '@tanstack/react-query'

import { resetLibraryUrlGuard } from '@/features/library/libraryCache'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
})

export function clearAuthQueryCache() {
  resetLibraryUrlGuard()
  queryClient.clear()
}
