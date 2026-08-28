import { useQuery } from '@tanstack/react-query'

import { fetchHealth, fetchModules } from '@/services/platformService'

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    staleTime: 30_000,
    retry: 1,
  })
}

export function useModules() {
  return useQuery({
    queryKey: ['modules'],
    queryFn: fetchModules,
    staleTime: 60_000,
  })
}
