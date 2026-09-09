import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
})

/** Clear all cached queries on auth transitions (AUTH-01). */
export function clearAuthQueryCache() {
  queryClient.clear()
}
