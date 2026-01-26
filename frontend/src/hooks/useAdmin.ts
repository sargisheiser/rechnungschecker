import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '@/lib/api'
import type { AdminUserUpdate, PlanTier } from '@/types'

export function useAdminStats() {
  return useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: () => adminApi.getStats(),
    staleTime: 1000 * 60, // 1 minute
  })
}

export function useAdminUsers(
  page = 1,
  pageSize = 20,
  search?: string,
  plan?: PlanTier,
  isActive?: boolean
) {
  return useQuery({
    queryKey: ['admin', 'users', page, pageSize, search, plan, isActive],
    queryFn: () => adminApi.listUsers(page, pageSize, search, plan, isActive),
    staleTime: 1000 * 30, // 30 seconds
  })
}

export function useAdminUser(userId: string | undefined) {
  return useQuery({
    queryKey: ['admin', 'user', userId],
    queryFn: () => adminApi.getUser(userId!),
    enabled: !!userId,
    staleTime: 1000 * 30, // 30 seconds
  })
}

export function useUpdateAdminUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: AdminUserUpdate }) =>
      adminApi.updateUser(userId, data),
    onSuccess: (updatedUser) => {
      queryClient.setQueryData(['admin', 'user', updatedUser.id], updatedUser)
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] })
    },
  })
}

export function useDeleteAdminUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (userId: string) => adminApi.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] })
    },
  })
}

export function useAdminAuditLogs(
  page = 1,
  pageSize = 50,
  userId?: string,
  action?: string
) {
  return useQuery({
    queryKey: ['admin', 'audit', page, pageSize, userId, action],
    queryFn: () => adminApi.getAuditLogs(page, pageSize, userId, action),
    staleTime: 1000 * 30, // 30 seconds
  })
}
