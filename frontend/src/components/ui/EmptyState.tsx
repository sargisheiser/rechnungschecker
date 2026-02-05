import { Link } from 'react-router-dom'
import { type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

// Preset illustrations as SVG components for common empty states
const illustrations = {
  // Document/File illustration
  documents: () => (
    <svg className="w-32 h-32" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="24" y="16" width="64" height="80" rx="4" className="fill-gray-100 stroke-gray-300" strokeWidth="2" />
      <rect x="40" y="32" width="72" height="80" rx="4" className="fill-white stroke-gray-300" strokeWidth="2" />
      <path d="M56 56H96" className="stroke-gray-300" strokeWidth="2" strokeLinecap="round" />
      <path d="M56 68H96" className="stroke-gray-300" strokeWidth="2" strokeLinecap="round" />
      <path d="M56 80H80" className="stroke-gray-300" strokeWidth="2" strokeLinecap="round" />
      <circle cx="96" cy="96" r="20" className="fill-primary-100 stroke-primary-300" strokeWidth="2" />
      <path d="M90 96L94 100L102 92" className="stroke-primary-500" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  // Users/Team illustration
  users: () => (
    <svg className="w-32 h-32" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="40" r="20" className="fill-gray-100 stroke-gray-300" strokeWidth="2" />
      <path d="M32 100C32 82.327 46.327 68 64 68C81.673 68 96 82.327 96 100" className="stroke-gray-300" strokeWidth="2" strokeLinecap="round" />
      <circle cx="100" cy="48" r="12" className="fill-primary-100 stroke-primary-300" strokeWidth="2" />
      <circle cx="28" cy="48" r="12" className="fill-primary-100 stroke-primary-300" strokeWidth="2" />
      <path d="M100 64C108 68 114 76 116 86" className="stroke-primary-300" strokeWidth="2" strokeLinecap="round" />
      <path d="M28 64C20 68 14 76 12 86" className="stroke-primary-300" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),

  // Key/Security illustration
  security: () => (
    <svg className="w-32 h-32" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="32" y="48" width="64" height="56" rx="8" className="fill-gray-100 stroke-gray-300" strokeWidth="2" />
      <path d="M64 24V48" className="stroke-gray-300" strokeWidth="2" />
      <circle cx="64" cy="24" r="16" className="fill-white stroke-gray-300" strokeWidth="2" />
      <circle cx="64" cy="76" r="8" className="fill-primary-100 stroke-primary-300" strokeWidth="2" />
      <path d="M64 84V92" className="stroke-primary-500" strokeWidth="3" strokeLinecap="round" />
    </svg>
  ),

  // Chart/Analytics illustration
  analytics: () => (
    <svg className="w-32 h-32" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="16" y="88" width="16" height="24" rx="2" className="fill-gray-200" />
      <rect x="40" y="64" width="16" height="48" rx="2" className="fill-gray-200" />
      <rect x="64" y="48" width="16" height="64" rx="2" className="fill-primary-200" />
      <rect x="88" y="32" width="16" height="80" rx="2" className="fill-primary-300" />
      <path d="M16 40L48 56L72 32L112 16" className="stroke-primary-500" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="16" cy="40" r="4" className="fill-primary-500" />
      <circle cx="48" cy="56" r="4" className="fill-primary-500" />
      <circle cx="72" cy="32" r="4" className="fill-primary-500" />
      <circle cx="112" cy="16" r="4" className="fill-primary-500" />
    </svg>
  ),

  // Search/Not found illustration
  search: () => (
    <svg className="w-32 h-32" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="52" cy="52" r="32" className="fill-gray-100 stroke-gray-300" strokeWidth="2" />
      <circle cx="52" cy="52" r="20" className="fill-white stroke-gray-300" strokeWidth="2" />
      <path d="M76 76L100 100" className="stroke-gray-400" strokeWidth="4" strokeLinecap="round" />
      <path d="M44 52H60" className="stroke-gray-300" strokeWidth="2" strokeLinecap="round" />
      <path d="M52 44V60" className="stroke-gray-300" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),

  // Folder/Empty illustration
  folder: () => (
    <svg className="w-32 h-32" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M16 36C16 32.686 18.686 30 22 30H48L56 40H106C109.314 40 112 42.686 112 46V96C112 99.314 109.314 102 106 102H22C18.686 102 16 99.314 16 96V36Z" className="fill-gray-100 stroke-gray-300" strokeWidth="2" />
      <path d="M32 60H96" className="stroke-gray-300" strokeWidth="2" strokeLinecap="round" strokeDasharray="4 4" />
      <path d="M32 76H80" className="stroke-gray-300" strokeWidth="2" strokeLinecap="round" strokeDasharray="4 4" />
    </svg>
  ),

  // Webhook illustration
  webhook: () => (
    <svg className="w-32 h-32" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="32" cy="64" r="16" className="fill-gray-100 stroke-gray-300" strokeWidth="2" />
      <circle cx="96" cy="32" r="16" className="fill-primary-100 stroke-primary-300" strokeWidth="2" />
      <circle cx="96" cy="96" r="16" className="fill-primary-100 stroke-primary-300" strokeWidth="2" />
      <path d="M48 64H64L80 40" className="stroke-gray-400" strokeWidth="2" strokeLinecap="round" />
      <path d="M64 64L80 88" className="stroke-gray-400" strokeWidth="2" strokeLinecap="round" />
      <circle cx="32" cy="64" r="4" className="fill-gray-400" />
      <circle cx="96" cy="32" r="4" className="fill-primary-500" />
      <circle cx="96" cy="96" r="4" className="fill-primary-500" />
    </svg>
  ),
}

type IllustrationType = keyof typeof illustrations

interface EmptyStateProps {
  /** Preset illustration type */
  illustration?: IllustrationType
  /** Custom icon (used if no illustration) */
  icon?: LucideIcon
  /** Main title */
  title: string
  /** Description text */
  description: string
  /** Primary action button */
  action?: {
    label: string
    onClick?: () => void
    href?: string
  }
  /** Secondary action link */
  secondaryAction?: {
    label: string
    onClick?: () => void
    href?: string
  }
  /** Additional CSS classes */
  className?: string
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
}

export function EmptyState({
  illustration,
  icon: Icon,
  title,
  description,
  action,
  secondaryAction,
  className,
  size = 'md',
}: EmptyStateProps) {
  const Illustration = illustration ? illustrations[illustration] : null

  const sizeClasses = {
    sm: {
      container: 'py-8',
      illustration: 'scale-75',
      icon: 'h-12 w-12',
      title: 'text-base',
      description: 'text-sm',
    },
    md: {
      container: 'py-12',
      illustration: 'scale-100',
      icon: 'h-16 w-16',
      title: 'text-lg',
      description: 'text-sm',
    },
    lg: {
      container: 'py-16',
      illustration: 'scale-110',
      icon: 'h-20 w-20',
      title: 'text-xl',
      description: 'text-base',
    },
  }

  const sizes = sizeClasses[size]

  return (
    <div className={cn('text-center', sizes.container, className)}>
      {/* Illustration or Icon */}
      <div className="flex justify-center mb-4">
        {Illustration ? (
          <div className={sizes.illustration}>
            <Illustration />
          </div>
        ) : Icon ? (
          <div className="p-4 bg-gray-100 rounded-full">
            <Icon className={cn(sizes.icon, 'text-gray-400')} />
          </div>
        ) : null}
      </div>

      {/* Title */}
      <h3 className={cn('font-semibold text-gray-900 mb-2', sizes.title)}>
        {title}
      </h3>

      {/* Description */}
      <p className={cn('text-gray-500 max-w-sm mx-auto mb-6', sizes.description)}>
        {description}
      </p>

      {/* Actions */}
      {(action || secondaryAction) && (
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          {action && (
            action.href ? (
              <Link to={action.href} className="btn-primary">
                {action.label}
              </Link>
            ) : (
              <button onClick={action.onClick} className="btn-primary">
                {action.label}
              </button>
            )
          )}
          {secondaryAction && (
            secondaryAction.href ? (
              <Link to={secondaryAction.href} className="btn-secondary">
                {secondaryAction.label}
              </Link>
            ) : (
              <button onClick={secondaryAction.onClick} className="btn-secondary">
                {secondaryAction.label}
              </button>
            )
          )}
        </div>
      )}
    </div>
  )
}

// Preset empty states for common use cases
export const emptyStatePresets = {
  noValidations: {
    illustration: 'documents' as IllustrationType,
    title: 'Keine Validierungen vorhanden',
    description: 'Laden Sie Ihre erste Rechnung hoch, um sie auf XRechnung- oder ZUGFeRD-Konformität zu prüfen.',
  },
  noSearchResults: {
    illustration: 'search' as IllustrationType,
    title: 'Keine Ergebnisse gefunden',
    description: 'Versuchen Sie es mit anderen Suchbegriffen oder Filtern.',
  },
  noClients: {
    illustration: 'users' as IllustrationType,
    title: 'Keine Mandanten angelegt',
    description: 'Legen Sie Ihren ersten Mandanten an, um Validierungen zuzuordnen und den Überblick zu behalten.',
  },
  noApiKeys: {
    illustration: 'security' as IllustrationType,
    title: 'Keine API-Schlüssel vorhanden',
    description: 'Erstellen Sie einen API-Schlüssel, um programmatischen Zugriff auf die Validierungs-API zu erhalten.',
  },
  noTemplates: {
    illustration: 'folder' as IllustrationType,
    title: 'Keine Vorlagen vorhanden',
    description: 'Erstellen Sie Vorlagen für häufig verwendete Absender- oder Empfängerdaten.',
  },
  noWebhooks: {
    illustration: 'webhook' as IllustrationType,
    title: 'Keine Webhooks konfiguriert',
    description: 'Richten Sie Webhooks ein, um bei Validierungsergebnissen automatisch benachrichtigt zu werden.',
  },
  noAnalytics: {
    illustration: 'analytics' as IllustrationType,
    title: 'Noch keine Daten verfügbar',
    description: 'Führen Sie einige Validierungen durch, um Ihre Statistiken und Trends zu sehen.',
  },
}
