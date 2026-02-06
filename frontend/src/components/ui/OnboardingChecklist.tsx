import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  CheckCircle2,
  Circle,
  FileCheck,
  User,
  ClipboardList,
  Sparkles,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface OnboardingTask {
  id: string
  title: string
  description: string
  icon: typeof FileCheck
  href?: string
  action?: string
}

const STORAGE_KEY = 'onboarding_completed_tasks'
const DISMISSED_KEY = 'onboarding_dismissed'

const defaultTasks: OnboardingTask[] = [
  {
    id: 'first_validation',
    title: 'Erste Rechnung validieren',
    description: 'Laden Sie eine XRechnung oder ZUGFeRD-Datei hoch',
    icon: FileCheck,
    action: 'Jetzt validieren',
  },
  {
    id: 'complete_profile',
    title: 'Profil vervollständigen',
    description: 'Fügen Sie Ihren Namen und Firmendaten hinzu',
    icon: User,
    href: '/einstellungen',
    action: 'Profil bearbeiten',
  },
  {
    id: 'create_template',
    title: 'Erste Vorlage erstellen',
    description: 'Speichern Sie häufig verwendete Absenderdaten',
    icon: ClipboardList,
    href: '/vorlagen',
    action: 'Vorlage erstellen',
  },
]

interface OnboardingChecklistProps {
  /** Tasks that are completed (from app state) */
  completedTaskIds?: string[]
  /** Custom class name */
  className?: string
  /** Callback when a task action is clicked */
  onTaskClick?: (taskId: string) => void
  /** Whether the user has completed their profile */
  hasCompletedProfile?: boolean
  /** Whether the user has at least one validation */
  hasValidations?: boolean
  /** Whether the user has at least one template */
  hasTemplates?: boolean
}

export function OnboardingChecklist({
  className,
  onTaskClick,
  hasCompletedProfile = false,
  hasValidations = false,
  hasTemplates = false,
}: OnboardingChecklistProps) {
  const [completedTasks, setCompletedTasks] = useState<Set<string>>(new Set())
  const [isDismissed, setIsDismissed] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState(false)

  // Load state from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    const dismissed = localStorage.getItem(DISMISSED_KEY)

    if (stored) {
      try {
        setCompletedTasks(new Set(JSON.parse(stored)))
      } catch {
        // Invalid stored data
      }
    }

    if (dismissed === 'true') {
      setIsDismissed(true)
    }
  }, [])

  // Sync external completion states
  useEffect(() => {
    const newCompleted = new Set(completedTasks)

    if (hasValidations && !completedTasks.has('first_validation')) {
      newCompleted.add('first_validation')
    }
    if (hasCompletedProfile && !completedTasks.has('complete_profile')) {
      newCompleted.add('complete_profile')
    }
    if (hasTemplates && !completedTasks.has('create_template')) {
      newCompleted.add('create_template')
    }

    if (newCompleted.size !== completedTasks.size) {
      setCompletedTasks(newCompleted)
      localStorage.setItem(STORAGE_KEY, JSON.stringify([...newCompleted]))
    }
  }, [hasValidations, hasCompletedProfile, hasTemplates, completedTasks])

  const handleDismiss = () => {
    setIsDismissed(true)
    localStorage.setItem(DISMISSED_KEY, 'true')
  }

  const handleTaskClick = (taskId: string) => {
    onTaskClick?.(taskId)
  }

  const completedCount = completedTasks.size
  const totalTasks = defaultTasks.length
  const allCompleted = completedCount === totalTasks
  const progressPercent = (completedCount / totalTasks) * 100

  // Don't render if dismissed or all tasks completed
  if (isDismissed || allCompleted) {
    return null
  }

  return (
    <div
      className={cn(
        'bg-gradient-to-br from-primary-50 to-white border border-primary-100 rounded-xl overflow-hidden',
        className
      )}
    >
      {/* Header */}
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-100 rounded-lg">
            <Sparkles className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Erste Schritte</h3>
            <p className="text-sm text-gray-500">
              {completedCount} von {totalTasks} erledigt
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label={isCollapsed ? 'Aufklappen' : 'Zuklappen'}
          >
            {isCollapsed ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronUp className="h-4 w-4" />
            )}
          </button>
          <button
            onClick={handleDismiss}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Schließen"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="px-4 pb-2">
        <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Tasks list */}
      {!isCollapsed && (
        <div className="px-4 pb-4 space-y-2">
          {defaultTasks.map((task) => {
            const isCompleted = completedTasks.has(task.id)
            const Icon = task.icon

            return (
              <div
                key={task.id}
                className={cn(
                  'flex items-start gap-3 p-3 rounded-lg transition-colors',
                  isCompleted ? 'bg-success-50/50' : 'bg-white hover:bg-gray-50'
                )}
              >
                {/* Checkbox */}
                <div className="flex-shrink-0 mt-0.5">
                  {isCompleted ? (
                    <CheckCircle2 className="h-5 w-5 text-success-500" />
                  ) : (
                    <Circle className="h-5 w-5 text-gray-300" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Icon
                      className={cn(
                        'h-4 w-4 flex-shrink-0',
                        isCompleted ? 'text-success-500' : 'text-gray-400'
                      )}
                    />
                    <span
                      className={cn(
                        'font-medium text-sm',
                        isCompleted
                          ? 'text-gray-500 line-through'
                          : 'text-gray-900'
                      )}
                    >
                      {task.title}
                    </span>
                  </div>
                  {!isCompleted && (
                    <p className="text-xs text-gray-500 mt-0.5 ml-6">
                      {task.description}
                    </p>
                  )}
                </div>

                {/* Action */}
                {!isCompleted && task.action && (
                  task.href ? (
                    <Link
                      to={task.href}
                      onClick={() => handleTaskClick(task.id)}
                      className="flex-shrink-0 text-xs font-medium text-primary-600 hover:text-primary-700"
                    >
                      {task.action} →
                    </Link>
                  ) : (
                    <button
                      onClick={() => handleTaskClick(task.id)}
                      className="flex-shrink-0 text-xs font-medium text-primary-600 hover:text-primary-700"
                    >
                      {task.action} →
                    </button>
                  )
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
