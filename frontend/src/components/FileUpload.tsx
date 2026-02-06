import { useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, AlertCircle, UserPlus } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { cn, isValidInvoiceFile } from '@/lib/utils'
import { useValidate, useValidationStore } from '@/hooks/useValidation'
import { ValidationProgress } from './ui/ValidationProgress'

interface FileUploadProps {
  className?: string
}

export function FileUpload({ className }: FileUploadProps) {
  const validate = useValidate()
  const { isValidating, guestLimitReached } = useValidationStore()
  const { t } = useTranslation()

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
      disabled: isValidating || guestLimitReached,
    })

  const hasError = fileRejections.length > 0 || (validate.isError && !guestLimitReached)

  // Show register prompt if guest limit reached
  if (guestLimitReached) {
    return (
      <div className={className}>
        <div className="border-2 border-dashed border-primary-300 rounded-xl p-8 bg-primary-50">
          <div className="flex flex-col items-center text-center">
            <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center mb-4">
              <UserPlus className="h-8 w-8 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              {t('upload.limitReached.title')}
            </h3>
            <p className="text-gray-600 mb-6 max-w-md">
              {t('upload.limitReached.description')}
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                to="/registrieren"
                className="btn-primary"
              >
                {t('upload.limitReached.register')}
              </Link>
              <Link
                to="/login"
                className="btn-secondary"
              >
                {t('nav.login')}
              </Link>
            </div>
          </div>
        </div>
      </div>
    )
  }

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
            <div className="py-4 w-full">
              <ValidationProgress isValidating={isValidating} />
            </div>
          ) : isDragActive ? (
            <>
              <Upload className="h-12 w-12 text-primary-600 mb-4" />
              <p className="text-lg font-medium text-primary-700">
                {t('upload.dropHere')}
              </p>
            </>
          ) : hasError ? (
            <>
              <AlertCircle className="h-12 w-12 text-error-500 mb-4" />
              <p className="text-lg font-medium text-error-600">
                {validate.isError
                  ? t('upload.validationError')
                  : t('upload.invalidFile')}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {validate.error?.message ||
                  t('upload.uploadXmlOrPdf')}
              </p>
            </>
          ) : (
            <>
              <div className="flex items-center gap-2 mb-4">
                <FileText className="h-10 w-10 text-gray-400" />
                <Upload className="h-6 w-6 text-primary-600" />
              </div>
              <p className="text-lg font-medium text-gray-900">
                {t('upload.title')}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {t('upload.dragOrClick')}
              </p>
              <p className="text-xs text-gray-400 mt-2">
                {t('upload.maxFileSize')}
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
