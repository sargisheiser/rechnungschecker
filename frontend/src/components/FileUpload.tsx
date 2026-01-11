import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, AlertCircle, Loader2 } from 'lucide-react'
import { cn, isValidInvoiceFile } from '@/lib/utils'
import { useValidate, useValidationStore } from '@/hooks/useValidation'

interface FileUploadProps {
  className?: string
}

export function FileUpload({ className }: FileUploadProps) {
  const validate = useValidate()
  const { isValidating } = useValidationStore()

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (file && isValidInvoiceFile(file.name)) {
        validate.mutate(file)
      }
    },
    [validate]
  )

  const { getRootProps, getInputProps, isDragActive, fileRejections } =
    useDropzone({
      onDrop,
      accept: {
        'application/xml': ['.xml'],
        'text/xml': ['.xml'],
        'application/pdf': ['.pdf'],
      },
      maxFiles: 1,
      maxSize: 10 * 1024 * 1024, // 10MB
      disabled: isValidating,
    })

  const hasError = fileRejections.length > 0 || validate.isError

  return (
    <div className={className}>
      <div
        {...getRootProps()}
        className={cn(
          'relative border-2 border-dashed rounded-xl p-8 transition-all cursor-pointer',
          'hover:border-primary-400 hover:bg-primary-50/50',
          isDragActive && 'border-primary-500 bg-primary-50',
          hasError && 'border-error-500 bg-error-50',
          isValidating && 'cursor-not-allowed opacity-60',
          !isDragActive && !hasError && 'border-gray-300 bg-white'
        )}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center text-center">
          {isValidating ? (
            <>
              <Loader2 className="h-12 w-12 text-primary-600 animate-spin mb-4" />
              <p className="text-lg font-medium text-gray-900">
                Rechnung wird validiert...
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Bitte warten Sie einen Moment
              </p>
            </>
          ) : isDragActive ? (
            <>
              <Upload className="h-12 w-12 text-primary-600 mb-4" />
              <p className="text-lg font-medium text-primary-700">
                Datei hier ablegen
              </p>
            </>
          ) : hasError ? (
            <>
              <AlertCircle className="h-12 w-12 text-error-500 mb-4" />
              <p className="text-lg font-medium text-error-600">
                {validate.isError
                  ? 'Fehler bei der Validierung'
                  : 'Ungueltige Datei'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {validate.error?.message ||
                  'Bitte laden Sie eine XML- oder PDF-Datei hoch'}
              </p>
            </>
          ) : (
            <>
              <div className="flex items-center gap-2 mb-4">
                <FileText className="h-10 w-10 text-gray-400" />
                <Upload className="h-6 w-6 text-primary-600" />
              </div>
              <p className="text-lg font-medium text-gray-900">
                E-Rechnung hier hochladen
              </p>
              <p className="text-sm text-gray-500 mt-1">
                XML (XRechnung) oder PDF (ZUGFeRD) ziehen oder klicken
              </p>
              <p className="text-xs text-gray-400 mt-2">
                Maximale Dateigrösse: 10 MB
              </p>
            </>
          )}
        </div>
      </div>

      {/* Supported formats info */}
      <div className="mt-4 flex flex-wrap justify-center gap-4 text-sm text-gray-500">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-success-500" />
          XRechnung
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-success-500" />
          ZUGFeRD 2.0/2.1
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-success-500" />
          Factur-X
        </div>
      </div>
    </div>
  )
}
