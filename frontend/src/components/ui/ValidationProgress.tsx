import { useEffect, useState } from 'react'
import { Upload, FileSearch, CheckCircle, Shield, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

type ValidationStep = 'uploading' | 'parsing' | 'validating' | 'complete'

interface ValidationProgressProps {
  /** Whether validation is in progress */
  isValidating: boolean
  /** Called when animation completes (optional) */
  onComplete?: () => void
  /** Custom class name */
  className?: string
}

const steps: { id: ValidationStep; label: string; icon: typeof Upload }[] = [
  { id: 'uploading', label: 'Hochladen', icon: Upload },
  { id: 'parsing', label: 'Analysieren', icon: FileSearch },
  { id: 'validating', label: 'Validieren', icon: Shield },
  { id: 'complete', label: 'Fertig', icon: CheckCircle },
]

export function ValidationProgress({
  isValidating,
  onComplete,
  className,
}: ValidationProgressProps) {
  const [currentStep, setCurrentStep] = useState<ValidationStep>('uploading')
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (!isValidating) {
      setCurrentStep('uploading')
      setProgress(0)
      return
    }

    // Simulate progress through steps
    const stepDurations = {
      uploading: 800,
      parsing: 1200,
      validating: 1500,
    }

    let timeout: ReturnType<typeof setTimeout>

    const advanceStep = () => {
      setCurrentStep((prev) => {
        if (prev === 'uploading') {
          timeout = setTimeout(advanceStep, stepDurations.parsing)
          return 'parsing'
        }
        if (prev === 'parsing') {
          timeout = setTimeout(advanceStep, stepDurations.validating)
          return 'validating'
        }
        // Stay on validating until actual completion
        return prev
      })
    }

    timeout = setTimeout(advanceStep, stepDurations.uploading)

    return () => clearTimeout(timeout)
  }, [isValidating])

  // Smooth progress bar animation
  useEffect(() => {
    if (!isValidating) return

    const stepProgress: Record<ValidationStep, number> = {
      uploading: 15,
      parsing: 45,
      validating: 75,
      complete: 100,
    }

    const targetProgress = stepProgress[currentStep]

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= targetProgress) {
          clearInterval(interval)
          return targetProgress
        }
        // Ease towards target
        const diff = targetProgress - prev
        return prev + Math.max(0.5, diff * 0.1)
      })
    }, 50)

    return () => clearInterval(interval)
  }, [currentStep, isValidating])

  // Handle completion
  useEffect(() => {
    if (!isValidating && currentStep !== 'uploading') {
      setCurrentStep('complete')
      setProgress(100)
      onComplete?.()
    }
  }, [isValidating, currentStep, onComplete])

  const currentStepIndex = steps.findIndex((s) => s.id === currentStep)

  return (
    <div className={cn('w-full max-w-md mx-auto', className)}>
      {/* Progress bar */}
      <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden mb-6">
        <div
          className="absolute inset-y-0 left-0 bg-gradient-to-r from-primary-500 to-primary-600 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
        {/* Shimmer effect */}
        <div
          className="absolute inset-y-0 left-0 w-full bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Steps */}
      <div className="flex justify-between">
        {steps.map((step, index) => {
          const Icon = step.icon
          const isActive = step.id === currentStep
          const isCompleted = index < currentStepIndex
          const isPending = index > currentStepIndex

          return (
            <div
              key={step.id}
              className={cn(
                'flex flex-col items-center transition-all duration-300',
                isActive && 'scale-110',
                isPending && 'opacity-40'
              )}
            >
              {/* Icon circle */}
              <div
                className={cn(
                  'relative w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300',
                  isCompleted && 'bg-success-100',
                  isActive && 'bg-primary-100',
                  isPending && 'bg-gray-100'
                )}
              >
                {isActive && step.id !== 'complete' ? (
                  <Loader2
                    className={cn(
                      'h-5 w-5 animate-spin',
                      'text-primary-600'
                    )}
                  />
                ) : (
                  <Icon
                    className={cn(
                      'h-5 w-5 transition-colors duration-300',
                      isCompleted && 'text-success-600',
                      isActive && 'text-primary-600',
                      isPending && 'text-gray-400'
                    )}
                  />
                )}

                {/* Pulse ring for active step */}
                {isActive && step.id !== 'complete' && (
                  <span className="absolute inset-0 rounded-full animate-ping bg-primary-400 opacity-20" />
                )}
              </div>

              {/* Label */}
              <span
                className={cn(
                  'mt-2 text-xs font-medium transition-colors duration-300',
                  isCompleted && 'text-success-600',
                  isActive && 'text-primary-600',
                  isPending && 'text-gray-400'
                )}
              >
                {step.label}
              </span>
            </div>
          )
        })}
      </div>

      {/* Current action text */}
      <div className="mt-6 text-center">
        <p className="text-sm text-gray-600">
          {currentStep === 'uploading' && 'Datei wird hochgeladen...'}
          {currentStep === 'parsing' && 'Datei wird analysiert...'}
          {currentStep === 'validating' && 'Validierungsregeln werden geprüft...'}
          {currentStep === 'complete' && 'Validierung abgeschlossen!'}
        </p>
      </div>
    </div>
  )
}
