import { useEffect, useCallback } from 'react'
import { AlertTriangle, Trash2, LogOut, XCircle, AlertCircle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

type DialogVariant = 'danger' | 'warning' | 'info'

interface ConfirmDialogProps {
  /** Whether the dialog is open */
  isOpen: boolean
  /** Called when dialog should close */
  onClose: () => void
  /** Called when user confirms */
  onConfirm: () => void
  /** Dialog title */
  title: string
  /** Dialog message/description */
  message: string | React.ReactNode
  /** Confirm button label */
  confirmLabel?: string
  /** Cancel button label */
  cancelLabel?: string
  /** Visual variant */
  variant?: DialogVariant
  /** Whether confirm action is loading */
  isLoading?: boolean
  /** Custom icon */
  icon?: 'trash' | 'logout' | 'warning' | 'error' | 'info'
}

const variantStyles = {
  danger: {
    iconBg: 'bg-error-100',
    iconColor: 'text-error-600',
    confirmBtn: 'bg-error-600 hover:bg-error-700 focus:ring-error-500',
  },
  warning: {
    iconBg: 'bg-warning-100',
    iconColor: 'text-warning-600',
    confirmBtn: 'bg-warning-600 hover:bg-warning-700 focus:ring-warning-500',
  },
  info: {
    iconBg: 'bg-primary-100',
    iconColor: 'text-primary-600',
    confirmBtn: 'bg-primary-600 hover:bg-primary-700 focus:ring-primary-500',
  },
}

const icons = {
  trash: Trash2,
  logout: LogOut,
  warning: AlertTriangle,
  error: XCircle,
  info: AlertCircle,
}

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Bestätigen',
  cancelLabel = 'Abbrechen',
  variant = 'danger',
  isLoading = false,
  icon = 'warning',
}: ConfirmDialogProps) {
  const styles = variantStyles[variant]
  const Icon = icons[icon]

  // Handle escape key
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isLoading) {
        onClose()
      }
    },
    [onClose, isLoading]
  )

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown)
      // Prevent body scroll when dialog is open
      document.body.style.overflow = 'hidden'
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
    }
  }, [isOpen, handleKeyDown])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={isLoading ? undefined : onClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        className="relative bg-white rounded-xl shadow-xl max-w-md w-full mx-auto transform transition-all"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
      >
        <div className="p-6">
          {/* Header with icon */}
          <div className="flex items-start gap-4">
            <div className={cn('p-3 rounded-full flex-shrink-0', styles.iconBg)}>
              <Icon className={cn('h-6 w-6', styles.iconColor)} />
            </div>
            <div className="flex-1 min-w-0">
              <h3
                id="confirm-dialog-title"
                className="text-lg font-semibold text-gray-900"
              >
                {title}
              </h3>
              <div className="mt-2 text-sm text-gray-600">
                {typeof message === 'string' ? <p>{message}</p> : message}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="mt-6 flex gap-3 sm:flex-row-reverse">
            <button
              type="button"
              onClick={onConfirm}
              disabled={isLoading}
              className={cn(
                'flex-1 sm:flex-none inline-flex justify-center items-center px-4 py-2.5 rounded-lg text-sm font-medium text-white transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed',
                styles.confirmBtn
              )}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Wird ausgeführt...
                </>
              ) : (
                confirmLabel
              )}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="flex-1 sm:flex-none inline-flex justify-center items-center px-4 py-2.5 rounded-lg text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {cancelLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Pre-configured dialog helpers for common use cases
export const confirmDialogPresets = {
  delete: {
    title: 'Löschen bestätigen',
    confirmLabel: 'Löschen',
    cancelLabel: 'Abbrechen',
    variant: 'danger' as DialogVariant,
    icon: 'trash' as const,
  },
  logout: {
    title: 'Abmelden',
    message: 'Möchten Sie sich wirklich abmelden?',
    confirmLabel: 'Abmelden',
    cancelLabel: 'Abbrechen',
    variant: 'warning' as DialogVariant,
    icon: 'logout' as const,
  },
  cancel: {
    title: 'Abbrechen bestätigen',
    confirmLabel: 'Ja, abbrechen',
    cancelLabel: 'Nein, fortfahren',
    variant: 'warning' as DialogVariant,
    icon: 'warning' as const,
  },
  deactivate: {
    title: 'Deaktivieren',
    confirmLabel: 'Deaktivieren',
    cancelLabel: 'Abbrechen',
    variant: 'warning' as DialogVariant,
    icon: 'warning' as const,
  },
}
