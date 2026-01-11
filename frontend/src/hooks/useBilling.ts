import { useQuery, useMutation } from '@tanstack/react-query'
import { billingApi } from '@/lib/api'
import { useAuthStore } from './useAuth'

export function usePlans() {
  return useQuery({
    queryKey: ['plans'],
    queryFn: async () => {
      const data = await billingApi.getPlans()
      return data.plans
    },
    staleTime: 1000 * 60 * 30, // 30 minutes
  })
}

export function usePlan(planId: string) {
  return useQuery({
    queryKey: ['plan', planId],
    queryFn: () => billingApi.getPlan(planId),
    enabled: !!planId,
    staleTime: 1000 * 60 * 30,
  })
}

export function useSubscription() {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ['subscription'],
    queryFn: () => billingApi.getSubscription(),
    enabled: isAuthenticated,
  })
}

export function useUsage() {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ['usage'],
    queryFn: () => billingApi.getUsage(),
    enabled: isAuthenticated,
  })
}

export function useCheckout() {
  return useMutation({
    mutationFn: async ({
      plan,
      annual,
    }: {
      plan: string
      annual: boolean
    }) => {
      const successUrl = `${window.location.origin}/dashboard?checkout=success`
      const cancelUrl = `${window.location.origin}/preise?checkout=canceled`
      const { url } = await billingApi.createCheckout(plan, annual, successUrl, cancelUrl)
      window.location.href = url
    },
  })
}

export function usePortalSession() {
  return useMutation({
    mutationFn: async () => {
      const returnUrl = `${window.location.origin}/dashboard`
      const { url } = await billingApi.createPortalSession(returnUrl)
      window.location.href = url
    },
  })
}

export function useCancelSubscription() {
  return useMutation({
    mutationFn: () => billingApi.cancelSubscription(),
  })
}
