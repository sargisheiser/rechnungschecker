import { useQuery, useMutation } from '@tanstack/react-query'
import { conversionApi } from '@/lib/api'
import type { OutputFormat, ZUGFeRDProfileType } from '@/types'

export function useConversionStatus() {
  return useQuery({
    queryKey: ['conversion-status'],
    queryFn: () => conversionApi.getStatus(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

export function usePreviewExtraction() {
  return useMutation({
    mutationFn: (file: File) => conversionApi.preview(file),
  })
}

export function useConvert() {
  return useMutation({
    mutationFn: ({
      file,
      outputFormat,
      zugferdProfile,
      embedInPdf,
      overrides,
    }: {
      file: File
      outputFormat?: OutputFormat
      zugferdProfile?: ZUGFeRDProfileType
      embedInPdf?: boolean
      overrides?: {
        invoice_number?: string
        seller_vat_id?: string
        buyer_reference?: string
        leitweg_id?: string
      }
    }) => conversionApi.convert(file, outputFormat, zugferdProfile, embedInPdf, overrides),
  })
}

export function useDownloadConversion() {
  return useMutation({
    mutationFn: async ({ conversionId, filename }: { conversionId: string; filename: string }) => {
      const blob = await conversionApi.download(conversionId)
      // Trigger download
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    },
  })
}
