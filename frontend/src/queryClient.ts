import { QueryClient } from '@tanstack/react-query'

import { resetLibraryUrlGuard } from '@/features/library/libraryCache'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
})

/** Clear all cached queries on auth transitions (AUTH-01). */
export function clearAuthQueryCache() {
  resetLibraryUrlGuard()
  queryClient.clear()
}
