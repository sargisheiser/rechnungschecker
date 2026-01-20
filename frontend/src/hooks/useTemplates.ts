import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { templatesApi } from '@/lib/api'
import { useAuthStore } from './useAuth'
import type { TemplateCreateRequest, TemplateUpdateRequest, TemplateType } from '@/types'

export function useTemplates(templateType?: TemplateType) {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ['templates', templateType],
    queryFn: () => templatesApi.list(1, 100, templateType),
    enabled: isAuthenticated,
  })
}

export function useTemplate(id: string | null) {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ['template', id],
    queryFn: () => templatesApi.get(id!),
    enabled: isAuthenticated && !!id,
  })
}

export function useCreateTemplate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: TemplateCreateRequest) => templatesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    },
  })
}

export function useUpdateTemplate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TemplateUpdateRequest }) =>
      templatesApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      queryClient.invalidateQueries({ queryKey: ['template', variables.id] })
    },
  })
}

export function useDeleteTemplate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => templatesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    },
  })
}

export function useSetDefaultTemplate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => templatesApi.setDefault(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    },
  })
}
