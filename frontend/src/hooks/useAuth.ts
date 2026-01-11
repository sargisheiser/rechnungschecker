import { create } from 'zustand'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi, setAccessToken, setRefreshToken, getAccessToken } from '@/lib/api'
import type { User, LoginRequest, RegisterRequest } from '@/types'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  setUser: (user: User | null) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  logout: () => {
    setAccessToken(null)
    setRefreshToken(null)
    set({ user: null, isAuthenticated: false })
  },
}))

export function useUser() {
  const { setUser } = useAuthStore()
  const hasToken = !!getAccessToken()

  return useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      const user = await authApi.getMe()
      setUser(user)
      return user
    },
    enabled: hasToken,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: false,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  const { setUser } = useAuthStore()

  return useMutation({
    mutationFn: async (data: LoginRequest) => {
      const tokens = await authApi.login(data)
      setAccessToken(tokens.access_token)
      setRefreshToken(tokens.refresh_token)
      const user = await authApi.getMe()
      return user
    },
    onSuccess: (user) => {
      setUser(user)
      queryClient.setQueryData(['user'], user)
    },
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  const { logout } = useAuthStore()

  return useMutation({
    mutationFn: async () => {
      try {
        await authApi.logout()
      } catch {
        // Ignore logout errors
      }
    },
    onSettled: () => {
      logout()
      queryClient.clear()
    },
  })
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: (email: string) => authApi.forgotPassword(email),
  })
}

export function useResetPassword() {
  return useMutation({
    mutationFn: ({ token, password }: { token: string; password: string }) =>
      authApi.resetPassword(token, password),
  })
}
