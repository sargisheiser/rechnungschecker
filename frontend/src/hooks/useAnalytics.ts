import { useQuery } from '@tanstack/react-query'
import { analyticsApi, AnalyticsDashboard, ClientComparison } from '@/lib/api'

export function useAnalyticsDashboard(days = 30, clientId?: string) {
  return useQuery<AnalyticsDashboard>({
    queryKey: ['analytics', 'dashboard', days, clientId],
    queryFn: () => analyticsApi.getDashboard(days, clientId),
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // 5 minutes
  })
}

export function useClientComparison(days = 30) {
  return useQuery<ClientComparison[]>({
    queryKey: ['analytics', 'clients', days],
    queryFn: () => analyticsApi.getClientComparison(days),
    staleTime: 60 * 1000,
    refetchInterval: 5 * 60 * 1000,
  })
}
