import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clientsApi } from '@/lib/api'
import { useAuthStore } from './useAuth'
import type { ClientCreateRequest, ClientUpdateRequest } from '@/types'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Store for selected client context
interface ClientContextStore {
  selectedClientId: string | null
  setSelectedClientId: (id: string | null) => void
}

export const useClientContext = create<ClientContextStore>()(
  persist(
    (set) => ({
      selectedClientId: null,
      setSelectedClientId: (id) => set({ selectedClientId: id }),
    }),
    {
      name: 'client-context',
    }
  )
)

export function useClients(page = 1, pageSize = 20, activeOnly = false, search?: string) {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ['clients', page, pageSize, activeOnly, search],
    queryFn: () => clientsApi.list(page, pageSize, activeOnly, search),
    enabled: isAuthenticated,
  })
}

export function useClientStats() {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ['client-stats'],
    queryFn: () => clientsApi.getStats(),
    enabled: isAuthenticated,
  })
}

export function useClient(id: string | null) {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ['client', id],
    queryFn: () => clientsApi.get(id!),
    enabled: isAuthenticated && !!id,
  })
}

export function useCreateClient() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ClientCreateRequest) => clientsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      queryClient.invalidateQueries({ queryKey: ['client-stats'] })
    },
  })
}

export function useUpdateClient() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ClientUpdateRequest }) =>
      clientsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      queryClient.invalidateQueries({ queryKey: ['client', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['client-stats'] })
    },
  })
}

export function useDeleteClient() {
  const queryClient = useQueryClient()
  const { selectedClientId, setSelectedClientId } = useClientContext()

  return useMutation({
    mutationFn: (id: string) => clientsApi.delete(id),
    onSuccess: (_, deletedId) => {
      // Clear selected client if it was deleted
      if (selectedClientId === deletedId) {
        setSelectedClientId(null)
      }
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      queryClient.invalidateQueries({ queryKey: ['client-stats'] })
    },
  })
}
