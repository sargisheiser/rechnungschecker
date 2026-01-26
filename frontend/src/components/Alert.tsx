import { ReactNode } from 'react'
import { AlertCircle, CheckCircle, Info, AlertTriangle, X } from 'lucide-react'
import { cn } from '@/lib/utils'

export type AlertVariant = 'success' | 'warning' | 'error' | 'info'

interface AlertProps {
  variant: AlertVariant
  title?: string
  children: ReactNode
  onDismiss?: () => void
  className?: string
}

const variantStyles: Record<AlertVariant, { container: string; icon: string; iconComponent: typeof AlertCircle }> = {
  success: {
    container: 'bg-success-50 border-success-200 text-success-800',
    icon: 'text-success-500',
    iconComponent: CheckCircle,
  },
  warning: {
    container: 'bg-warning-50 border-warning-200 text-warning-800',
    icon: 'text-warning-500',
    iconComponent: AlertTriangle,
  },
  error: {
    container: 'bg-error-50 border-error-200 text-error-800',
    icon: 'text-error-500',
    iconComponent: AlertCircle,
  },
  info: {
    container: 'bg-primary-50 border-primary-200 text-primary-800',
    icon: 'text-primary-500',
    iconComponent: Info,
  },
}

export function Alert({ variant, title, children, onDismiss, className }: AlertProps) {
  const styles = variantStyles[variant]
  const IconComponent = styles.iconComponent

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border',
        styles.container,
        className
      )}
      role="alert"
    >
      <IconComponent className={cn('h-5 w-5 flex-shrink-0 mt-0.5', styles.icon)} />
      <div className="flex-1 min-w-0">
        {title && <h4 className="font-medium mb-1">{title}</h4>}
        <div className="text-sm">{children}</div>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="flex-shrink-0 p-1 rounded-md hover:bg-black/5 transition-colors"
          aria-label="Schliessen"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}
