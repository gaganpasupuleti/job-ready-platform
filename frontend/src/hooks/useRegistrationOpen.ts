import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import { canOfferRegistration } from '@/lib/authPolicy'

export function useRegistrationOpen() {
  const query = useQuery({
    queryKey: ['auth-public-config'],
    queryFn: async () => {
      const { data } = await apiClient.get<{ public_registration_enabled: boolean }>(
        apiEndpoints.auth.config,
      )
      return canOfferRegistration(data.public_registration_enabled)
    },
    staleTime: 60_000,
  })
  return { open: query.data === true, pending: query.isPending }
}
