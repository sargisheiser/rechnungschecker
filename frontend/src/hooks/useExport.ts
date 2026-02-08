import { useMutation } from '@tanstack/react-query'
import { exportApi } from '@/lib/api'
import { toast, toastMessages } from '@/lib/toast'

export interface DATEVExportParams {
  validationIds: string[]
  kontenrahmen?: 'SKR03' | 'SKR04'
  debitorKonto?: string
  beraterNummer?: string
  mandantenNummer?: string
}

// Add DATEV export function to api
const datevApi = {
  downloadBuchungsstapel: async (params: DATEVExportParams): Promise<Blob> => {
    const queryParams = new URLSearchParams()

    // Add each validation ID as a separate query parameter
    params.validationIds.forEach((id) => {
      queryParams.append('validation_ids', id)
    })

    if (params.kontenrahmen) {
      queryParams.set('kontenrahmen', params.kontenrahmen)
    }
    if (params.debitorKonto) {
      queryParams.set('debitor_konto', params.debitorKonto)
    }
    if (params.beraterNummer) {
      queryParams.set('berater_nummer', params.beraterNummer)
    }
    if (params.mandantenNummer) {
      queryParams.set('mandanten_nummer', params.mandantenNummer)
    }

    // Use fetch directly to avoid axios interceptor issues with blob
    const token = localStorage.getItem('access_token')
    const response = await fetch(`/api/v1/export/datev/buchungsstapel?${queryParams}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Export fehlgeschlagen' }))
      throw new Error(error.detail || 'Export fehlgeschlagen')
    }

    return response.blob()
  },
}

export function useExportDATEV() {
  return useMutation({
    mutationFn: async (params: DATEVExportParams) => {
      if (params.validationIds.length === 0) {
        throw new Error('Keine Validierungen ausgewaehlt')
      }

      const blob = await datevApi.downloadBuchungsstapel(params)

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const today = new Date().toISOString().slice(0, 10).replace(/-/g, '')
      a.download = `EXTF_Buchungsstapel_${today}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      return { success: true, count: params.validationIds.length }
    },
    onSuccess: (result) => {
      toast.success(
        'DATEV Export erfolgreich',
        `${result.count} Buchung(en) wurden exportiert.`
      )
    },
    onError: (error: Error) => {
      toast.error('DATEV Export fehlgeschlagen', error.message)
    },
  })
}

export function useExportValidations() {
  return useMutation({
    mutationFn: async (params: {
      clientId?: string
      dateFrom?: string
      dateTo?: string
      status?: 'all' | 'valid' | 'invalid'
      format?: 'datev' | 'excel'
    }) => {
      const blob = await exportApi.downloadValidations(params)

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const today = new Date().toISOString().slice(0, 10).replace(/-/g, '')
      a.download = `validierungen_${today}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    },
    onSuccess: () => {
      toast.success(toastMessages.downloadSuccess)
    },
    onError: () => {
      toast.error(toastMessages.downloadError)
    },
  })
}

export function useExportClients() {
  return useMutation({
    mutationFn: async (params: {
      includeInactive?: boolean
      dateFrom?: string
      dateTo?: string
      format?: 'datev' | 'excel'
    }) => {
      const blob = await exportApi.downloadClients({
        include_inactive: params.includeInactive,
        date_from: params.dateFrom,
        date_to: params.dateTo,
        format: params.format,
      })

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const today = new Date().toISOString().slice(0, 10).replace(/-/g, '')
      a.download = `mandanten_${today}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    },
    onSuccess: () => {
      toast.success(toastMessages.downloadSuccess)
    },
    onError: () => {
      toast.error(toastMessages.downloadError)
    },
  })
}
