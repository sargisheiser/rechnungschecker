import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiKeysApi } from '@/lib/api'
import { useAuthStore } from './useAuth'
import type { APIKeyCreateRequest } from '@/types'

export function useAPIKeys() {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ['api-keys'],
    queryFn: () => apiKeysApi.list(),
    enabled: isAuthenticated,
  })
}

export function useCreateAPIKey() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: APIKeyCreateRequest) => apiKeysApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    },
  })
}

export function useUpdateAPIKey() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name?: string; description?: string; is_active?: boolean } }) =>
      apiKeysApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    },
  })
}

export function useDeleteAPIKey() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => apiKeysApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    },
  })
}
