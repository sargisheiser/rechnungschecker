import { useState, useEffect, useMemo } from 'react'
import { Maximize2, FileText, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PdfPreviewProps {
  file: File
  className?: string
}

export function PdfPreview({ file, className }: PdfPreviewProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // Create blob URL for the PDF
  const pdfUrl = useMemo(() => {
    return URL.createObjectURL(file)
  }, [file])

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      URL.revokeObjectURL(pdfUrl)
    }
  }, [pdfUrl])

  return (
    <>
      {/* Preview Panel */}
      <div className={cn('card overflow-hidden', className)}>
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-primary-500" />
            <span className="text-sm font-medium text-gray-700">PDF Vorschau</span>
          </div>
          <button
            onClick={() => setIsExpanded(true)}
            className="p-1.5 rounded-md hover:bg-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            title="Vollbild"
            aria-label="PDF im Vollbild anzeigen"
          >
            <Maximize2 className="h-4 w-4 text-gray-500" aria-hidden="true" />
          </button>
        </div>
        <div className="relative bg-gray-100" style={{ height: '500px' }}>
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto mb-2"></div>
                <p className="text-sm text-gray-500">PDF wird geladen...</p>
              </div>
            </div>
          )}
          <iframe
            src={`${pdfUrl}#toolbar=0&navpanes=0`}
            className="w-full h-full border-0"
            onLoad={() => setIsLoading(false)}
            title="PDF Vorschau"
          />
        </div>
      </div>

      {/* Fullscreen Modal */}
      {isExpanded && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-label="PDF Vollbildansicht"
        >
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl h-[90vh] flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary-500" />
                <span className="font-medium text-gray-900">{file.name}</span>
                <span className="text-sm text-gray-500">
                  ({(file.size / 1024).toFixed(1)} KB)
                </span>
              </div>
              <button
                onClick={() => setIsExpanded(false)}
                className="p-2 rounded-md hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                title="Schliessen"
                aria-label="Vollbildmodus schließen"
              >
                <X className="h-5 w-5 text-gray-500" aria-hidden="true" />
              </button>
            </div>
            <div className="flex-1 bg-gray-100">
              <iframe
                src={pdfUrl}
                className="w-full h-full border-0"
                title="PDF Vollbild"
              />
            </div>
          </div>
        </div>
      )}
    </>
  )
}
