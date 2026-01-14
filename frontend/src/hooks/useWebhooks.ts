import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { webhooksApi } from '@/lib/api'
import { useAuthStore } from './useAuth'
import type { WebhookCreateRequest, WebhookUpdateRequest } from '@/types'

export function useWebhooks() {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ['webhooks'],
    queryFn: () => webhooksApi.list(),
    enabled: isAuthenticated,
  })
}

export function useWebhook(id: string) {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ['webhooks', id],
    queryFn: () => webhooksApi.get(id),
    enabled: isAuthenticated && !!id,
  })
}

export function useCreateWebhook() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: WebhookCreateRequest) => webhooksApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] })
    },
  })
}

export function useUpdateWebhook() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WebhookUpdateRequest }) =>
      webhooksApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] })
    },
  })
}

export function useDeleteWebhook() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => webhooksApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] })
    },
  })
}

export function useTestWebhook() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => webhooksApi.test(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] })
    },
  })
}

export function useRotateWebhookSecret() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => webhooksApi.rotateSecret(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] })
    },
  })
}
