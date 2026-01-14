import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { integrationsApi } from '@/lib/api'
import { useAuthStore } from './useAuth'
import type { IntegrationType, IntegrationCreateRequest, IntegrationUpdateRequest } from '@/types'

export function useIntegrations() {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ['integrations'],
    queryFn: () => integrationsApi.list(),
    enabled: isAuthenticated,
  })
}

export function useCreateIntegration() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ type, data }: { type: IntegrationType; data: IntegrationCreateRequest }) =>
      integrationsApi.create(type, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] })
    },
  })
}

export function useUpdateIntegration() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ type, data }: { type: IntegrationType; data: IntegrationUpdateRequest }) =>
      integrationsApi.update(type, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] })
    },
  })
}

export function useDeleteIntegration() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (type: IntegrationType) => integrationsApi.delete(type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] })
    },
  })
}

export function useTestIntegration() {
  return useMutation({
    mutationFn: (type: IntegrationType) => integrationsApi.test(type),
  })
}
