import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { X, ChevronRight, ChevronLeft, FileCheck, History, ArrowRightLeft, Settings, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

const ONBOARDING_STORAGE_KEY = 'rechnungschecker_onboarding'

interface OnboardingStep {
  id: string
  title: string
  description: string
  icon: typeof FileCheck
  link?: string
  linkText?: string
}

const STEPS: OnboardingStep[] = [
  {
    id: 'welcome',
    title: 'Willkommen bei RechnungsChecker!',
    description: 'Wir zeigen Ihnen in wenigen Schritten, wie Sie das Beste aus unserem Service herausholen.',
    icon: Sparkles,
  },
  {
    id: 'upload',
    title: 'Rechnung validieren',
    description: 'Laden Sie eine XRechnung (XML) oder ZUGFeRD (PDF) hoch. Wir pruefen sie sofort auf Konformitaet.',
    icon: FileCheck,
  },
  {
    id: 'history',
    title: 'Validierungshistorie',
    description: 'Alle Ihre Validierungen werden gespeichert. Sie finden sie jederzeit im Dashboard unter "Letzte Validierungen".',
    icon: History,
  },
  {
    id: 'conversion',
    title: 'PDF zu XRechnung',
    description: 'Mit der Konvertierung wandeln Sie normale PDF-Rechnungen in XRechnung-Format um - mit KI-Unterstuetzung.',
    icon: ArrowRightLeft,
    link: '/konvertierung',
    linkText: 'Zur Konvertierung',
  },
  {
    id: 'settings',
    title: 'Einstellungen anpassen',
    description: 'Passen Sie Benachrichtigungen und Ihr Profil nach Ihren Wuenschen an.',
    icon: Settings,
    link: '/einstellungen',
    linkText: 'Zu den Einstellungen',
  },
]

interface OnboardingTourProps {
  userCreatedAt: string
  onComplete?: () => void
}

export function OnboardingTour({ userCreatedAt, onComplete }: OnboardingTourProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    // Check if user is new (registered within last 7 days)
    const createdDate = new Date(userCreatedAt)
    const now = new Date()
    const daysSinceCreation = (now.getTime() - createdDate.getTime()) / (1000 * 60 * 60 * 24)

    if (daysSinceCreation > 7) {
      return
    }

    // Check if onboarding was already completed or dismissed
    const onboardingData = localStorage.getItem(ONBOARDING_STORAGE_KEY)
    if (onboardingData) {
      const { completed, dismissed } = JSON.parse(onboardingData)
      if (completed || dismissed) {
        return
      }
    }

    // Show onboarding
    setIsVisible(true)
  }, [userCreatedAt])

  const handleNext = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      handleComplete()
    }
  }

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleComplete = () => {
    localStorage.setItem(ONBOARDING_STORAGE_KEY, JSON.stringify({ completed: true, completedAt: new Date().toISOString() }))
    setIsVisible(false)
    onComplete?.()
  }

  const handleDismiss = () => {
    localStorage.setItem(ONBOARDING_STORAGE_KEY, JSON.stringify({ dismissed: true, dismissedAt: new Date().toISOString() }))
    setIsVisible(false)
  }

  if (!isVisible) {
    return null
  }

  const step = STEPS[currentStep]
  const IconComponent = step.icon
  const isLastStep = currentStep === STEPS.length - 1

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary-500 to-primary-600 p-6 text-white">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-lg">
                <IconComponent className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs text-primary-100">Schritt {currentStep + 1} von {STEPS.length}</p>
                <h3 className="text-lg font-semibold">{step.title}</h3>
              </div>
            </div>
            <button
              onClick={handleDismiss}
              className="p-1 hover:bg-white/20 rounded-lg transition-colors"
              aria-label="Schliessen"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-gray-600 mb-4">{step.description}</p>

          {step.link && (
            <Link
              to={step.link}
              onClick={handleComplete}
              className="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 font-medium text-sm"
            >
              {step.linkText}
              <ChevronRight className="h-4 w-4" />
            </Link>
          )}

          {/* Progress dots */}
          <div className="flex items-center justify-center gap-2 mt-6">
            {STEPS.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentStep(index)}
                className={cn(
                  'w-2 h-2 rounded-full transition-colors',
                  index === currentStep ? 'bg-primary-500' : 'bg-gray-200 hover:bg-gray-300'
                )}
                aria-label={`Zu Schritt ${index + 1}`}
              />
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 flex items-center justify-between">
          <button
            onClick={handlePrev}
            disabled={currentStep === 0}
            className={cn(
              'flex items-center gap-1 text-sm font-medium',
              currentStep === 0 ? 'text-gray-300 cursor-not-allowed' : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <ChevronLeft className="h-4 w-4" />
            Zurück
          </button>

          <div className="flex items-center gap-3">
            <button
              onClick={handleDismiss}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Ueberspringen
            </button>
            <button
              onClick={handleNext}
              className="btn-primary text-sm px-4 py-2"
            >
              {isLastStep ? 'Fertig' : 'Weiter'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
