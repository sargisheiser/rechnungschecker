import { create } from 'zustand'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { AxiosError } from 'axios'
import { validationApi } from '@/lib/api'
import { getGuestId } from '@/lib/utils'
import type { ValidationResult } from '@/types'
import { useAuthStore } from './useAuth'

interface ValidationState {
  currentResult: ValidationResult | null
  isValidating: boolean
  guestLimitReached: boolean
  setResult: (result: ValidationResult | null) => void
  setValidating: (validating: boolean) => void
  setGuestLimitReached: (reached: boolean) => void
  clearResult: () => void
}

export const useValidationStore = create<ValidationState>((set) => ({
  currentResult: null,
  isValidating: false,
  guestLimitReached: false,
  setResult: (result) => set({ currentResult: result, isValidating: false }),
  setValidating: (isValidating) => set({ isValidating }),
  setGuestLimitReached: (guestLimitReached) => set({ guestLimitReached }),
  clearResult: () => set({ currentResult: null, guestLimitReached: false }),
}))

export function useValidate() {
  const { setResult, setValidating, setGuestLimitReached } = useValidationStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (file: File) => {
      setValidating(true)
      // Get current auth state at mutation time
      const { isAuthenticated } = useAuthStore.getState()
      if (isAuthenticated) {
        return validationApi.validate(file)
      } else {
        const guestId = getGuestId()
        const result = await validationApi.validateGuest(file, guestId)
        // Store guest_id if returned
        if (result.guest_id) {
          localStorage.setItem('guest_id', result.guest_id)
        }
        return result
      }
    },
    onSuccess: (result) => {
      setResult(result)
      // Invalidate history if authenticated (get fresh state)
      const { isAuthenticated } = useAuthStore.getState()
      if (isAuthenticated) {
        queryClient.invalidateQueries({ queryKey: ['validation-history'] })
      }
    },
    onError: (error: AxiosError<{ detail?: { code?: string } }>) => {
      setValidating(false)
      // Check if guest limit reached (403 with code GUEST_LIMIT_REACHED)
      if (error.response?.status === 403) {
        const detail = error.response?.data?.detail
        if (detail?.code === 'GUEST_LIMIT_REACHED') {
          setGuestLimitReached(true)
        }
      }
    },
  })
}

export function useValidationHistory(page = 1, limit = 10) {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ['validation-history', page, limit],
    queryFn: () => validationApi.getHistory(page, limit),
    enabled: isAuthenticated,
  })
}

export function useValidationResult(id: string) {
  return useQuery({
    queryKey: ['validation-result', id],
    queryFn: () => validationApi.getResult(id),
    enabled: !!id,
  })
}

export function useDownloadReport() {
  return useMutation({
    mutationFn: async (id: string) => {
      const blob = await validationApi.downloadReport(id)
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `validierungsbericht-${id}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    },
  })
}
