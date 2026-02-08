import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { Check, X, Loader2, AlertCircle, Shield } from 'lucide-react'
import { usePlans, useCheckout, useSubscription } from '@/hooks/useBilling'
import { useAuthStore } from '@/hooks/useAuth'
import { cn, formatCurrency } from '@/lib/utils'
import type { Plan, PlanTier } from '@/types'

// Fallback plans if API is unavailable
const FALLBACK_PLANS: Plan[] = [
  {
    id: 'free' as PlanTier,
    name: 'Kostenlos',
    description: 'Fuer Einsteiger',
    price_monthly: 0,
    price_annual: 0,
    popular: false,
    features: {
      validations_per_month: 5,
      conversions_per_month: 0,
      batch_upload: false,
      api_access: false,
      api_calls_per_month: 0,
      report_download: false,
      multi_client: false,
      max_clients: 0,
      support_level: 'community',
    },
  },
  {
    id: 'starter' as PlanTier,
    name: 'Starter',
    description: 'Fuer kleine Unternehmen',
    price_monthly: 29,
    price_annual: 299,
    popular: false,
    features: {
      validations_per_month: 100,
      conversions_per_month: 50,
      batch_upload: false,
      api_access: false,
      api_calls_per_month: 0,
      report_download: true,
      multi_client: false,
      max_clients: 0,
      support_level: 'email',
    },
  },
  {
    id: 'pro' as PlanTier,
    name: 'Professional',
    description: 'Fuer wachsende Unternehmen',
    price_monthly: 79,
    price_annual: 799,
    popular: true,
    features: {
      validations_per_month: null,
      conversions_per_month: 200,
      batch_upload: true,
      api_access: true,
      api_calls_per_month: 10000,
      report_download: true,
      multi_client: false,
      max_clients: 0,
      support_level: 'priority',
    },
  },
  {
    id: 'steuerberater' as PlanTier,
    name: 'Steuerberater',
    description: 'Fuer Kanzleien',
    price_monthly: 199,
    price_annual: 1999,
    popular: false,
    features: {
      validations_per_month: null,
      conversions_per_month: 999999,
      batch_upload: true,
      api_access: true,
      api_calls_per_month: 100000,
      report_download: true,
      multi_client: true,
      max_clients: 100,
      support_level: 'phone',
    },
  },
]

export function Pricing() {
  const [annual, setAnnual] = useState(true)
  const [checkoutError, setCheckoutError] = useState<string | null>(null)
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { data: apiPlans, isLoading, error } = usePlans()
  const { isAuthenticated, user } = useAuthStore()
  const { data: subscription } = useSubscription()
  const checkout = useCheckout()

  // Use API plans if available, otherwise fallback
  const plans = apiPlans && apiPlans.length > 0 ? apiPlans : (error ? FALLBACK_PLANS : undefined)

  const checkoutCanceled = searchParams.get('checkout') === 'canceled'

  // Check if user has an active paid subscription
  const hasActiveSubscription = isAuthenticated && subscription && subscription.plan !== 'free'
  const currentPlan = subscription?.plan || user?.plan || 'free'

  // Clear error when changing annual/monthly
  useEffect(() => {
    setCheckoutError(null)
  }, [annual])

  const handleSelectPlan = (planId: PlanTier) => {
    setCheckoutError(null)

    if (planId === 'free') {
      // Redirect to register for free plan
      window.location.href = '/registrieren'
      return
    }

    if (!isAuthenticated) {
      // Redirect to register first
      window.location.href = `/registrieren?plan=${planId}&annual=${annual}`
      return
    }

    // If user has active subscription, redirect to billing portal
    if (hasActiveSubscription) {
      navigate('/einstellungen')
      return
    }

    checkout.mutate(
      { plan: planId, annual },
      {
        onError: (err: unknown) => {
          const axiosError = err as { response?: { data?: { detail?: string } } }
          const message = axiosError.response?.data?.detail || 'Checkout fehlgeschlagen. Bitte versuchen Sie es erneut.'
          setCheckoutError(message)
        },
      }
    )
  }

  return (
    <div className="py-16 lg:py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h1 className="text-4xl font-bold text-gray-900">
            Einfache, transparente Preise
          </h1>
          <p className="mt-4 text-lg text-gray-600">
            Wählen Sie den passenden Plan für Ihr Unternehmen. Keine
            versteckten Kosten.
          </p>

          {checkoutCanceled && (
            <div className="mt-6 p-4 bg-warning-50 border border-warning-200 rounded-lg inline-flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-warning-600" />
              <span className="text-warning-700">
                Checkout abgebrochen. Sie können jederzeit erneut starten.
              </span>
            </div>
          )}

          {checkoutError && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg inline-flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <span className="text-red-700">{checkoutError}</span>
            </div>
          )}

          {hasActiveSubscription && (
            <div className="mt-6 p-4 bg-primary-50 border border-primary-200 rounded-lg inline-flex items-center gap-3">
              <Check className="h-5 w-5 text-primary-600" />
              <span className="text-primary-700">
                Sie haben bereits ein aktives <strong>{currentPlan}</strong>-Abonnement.{' '}
                <button
                  onClick={() => navigate('/einstellungen')}
                  className="underline hover:no-underline"
                >
                  Abonnement verwalten
                </button>
              </span>
            </div>
          )}

          {/* Billing toggle */}
          <div className="mt-8 flex items-center justify-center gap-4">
            <span
              className={cn(
                'text-sm font-medium',
                !annual ? 'text-gray-900' : 'text-gray-500'
              )}
            >
              Monatlich
            </span>
            <button
              onClick={() => setAnnual(!annual)}
              className={cn(
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                annual ? 'bg-primary-600' : 'bg-gray-200'
              )}
            >
              <span
                className={cn(
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  annual ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </button>
            <span
              className={cn(
                'text-sm font-medium',
                annual ? 'text-gray-900' : 'text-gray-500'
              )}
            >
              Jaehrlich
            </span>
            {annual && (
              <span className="text-xs bg-success-100 text-success-700 px-2 py-1 rounded-full font-medium">
                2 Monate gratis
              </span>
            )}
          </div>

          {/* Money-back Guarantee */}
          <div className="mt-6 flex items-center justify-center gap-2 text-sm text-gray-600">
            <Shield className="h-5 w-5 text-success-500" />
            <span>
              <strong className="text-gray-900">30 Tage Geld-zurück-Garantie</strong> - Nicht zufrieden? Volle Erstattung, keine Fragen.
            </span>
          </div>
        </div>

        {/* Plans */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : !plans || plans.length === 0 ? (
          <div className="text-center py-12">
            <AlertCircle className="h-12 w-12 text-warning-500 mx-auto mb-4" />
            <p className="text-gray-600">Keine Preisplaene verfuegbar.</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mt-6 isolate">
            {plans.map((plan) => (
              <PlanCard
                key={plan.id}
                plan={plan}
                annual={annual}
                onSelect={() => handleSelectPlan(plan.id)}
                isLoading={checkout.isPending}
                isAuthenticated={isAuthenticated}
                isCurrentPlan={plan.id === currentPlan}
                hasActiveSubscription={hasActiveSubscription || false}
              />
            ))}
          </div>
        )}

        {/* FAQ */}
        <div className="mt-16 max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
            Haeufige Fragen
          </h2>
          <div className="space-y-6">
            <FaqItem
              question="Kann ich den Plan jederzeit wechseln?"
              answer="Ja, Sie können jederzeit auf einen anderen Plan wechseln. Bei einem Upgrade wird der Preisunterschied anteilig berechnet."
            />
            <FaqItem
              question="Gibt es eine Kuendigungsfrist?"
              answer="Nein, Sie können Ihr Abonnement jederzeit kündigen. Es läuft dann zum Ende der aktuellen Abrechnungsperiode aus."
            />
            <FaqItem
              question="Was passiert mit meinen Daten nach der Kuendigung?"
              answer="Ihre Validierungshistorie bleibt 30 Tage nach Kuendigung erhalten. Danach werden alle Daten geloescht."
            />
            <FaqItem
              question="Bieten Sie Rabatte für groessere Teams?"
              answer="Ja, für Unternehmen mit mehr als 10 Nutzern bieten wir individuelle Konditionen. Kontaktieren Sie uns."
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function PlanCard({
  plan,
  annual,
  onSelect,
  isLoading,
  isAuthenticated,
  isCurrentPlan,
  hasActiveSubscription,
}: {
  plan: Plan
  annual: boolean
  onSelect: () => void
  isLoading: boolean
  isAuthenticated: boolean
  isCurrentPlan: boolean
  hasActiveSubscription: boolean
}) {
  const price = annual ? plan.price_annual : plan.price_monthly
  const monthlyEquivalent = annual ? plan.price_annual / 12 : plan.price_monthly

  const features = [
    {
      label:
        plan.features.validations_per_month === null
          ? 'Unbegrenzte Validierungen'
          : `${plan.features.validations_per_month} Validierungen/Monat`,
      included: true,
    },
    {
      label:
        plan.features.conversions_per_month === 0
          ? 'Keine Konvertierungen'
          : `${plan.features.conversions_per_month} Konvertierungen/Monat`,
      included: plan.features.conversions_per_month > 0,
    },
    { label: 'Batch-Upload', included: plan.features.batch_upload },
    { label: 'API-Zugang', included: plan.features.api_access },
    { label: 'PDF-Berichte', included: plan.features.report_download },
    { label: 'Mandantenverwaltung', included: plan.features.multi_client },
  ]

  return (
    <div
      className={cn(
        'card flex flex-col relative overflow-visible',
        isCurrentPlan && 'ring-2 ring-success-500',
        plan.popular && !isCurrentPlan && 'ring-2 ring-primary-500'
      )}
    >
      {isCurrentPlan && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 pointer-events-none">
          <span className="bg-success-500 text-white text-xs font-medium px-3 py-1 rounded-full">
            Aktuell
          </span>
        </div>
      )}
      {plan.popular && !isCurrentPlan && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 pointer-events-none">
          <span className="bg-primary-500 text-white text-xs font-medium px-3 py-1 rounded-full">
            Beliebt
          </span>
        </div>
      )}

      <div className="p-6 flex-1">
        <h3 className="text-lg font-semibold text-gray-900">{plan.name}</h3>
        <p className="text-sm text-gray-500 mt-1">{plan.description}</p>

        <div className="mt-4">
          <span className="text-4xl font-bold text-gray-900">
            {formatCurrency(price)}
          </span>
          <span className="text-gray-500">/{annual ? 'Jahr' : 'Monat'}</span>
          {annual && price > 0 && (
            <p className="text-sm text-gray-500 mt-1">
              entspricht {formatCurrency(monthlyEquivalent)}/Monat
            </p>
          )}
        </div>

        <ul className="mt-6 space-y-3">
          {features.map((feature, index) => (
            <li key={index} className="flex items-start gap-2">
              {feature.included ? (
                <Check className="h-5 w-5 text-success-500 flex-shrink-0" />
              ) : (
                <X className="h-5 w-5 text-gray-300 flex-shrink-0" />
              )}
              <span
                className={cn(
                  'text-sm',
                  feature.included ? 'text-gray-700' : 'text-gray-400'
                )}
              >
                {feature.label}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="p-6 pt-0 relative z-30">
        <button
          onClick={(e) => {
            e.stopPropagation()
            onSelect()
          }}
          disabled={isLoading || isCurrentPlan}
          className={cn(
            'w-full cursor-pointer',
            isCurrentPlan
              ? 'btn-secondary opacity-70 cursor-not-allowed'
              : plan.popular
                ? 'btn-primary'
                : 'btn-secondary'
          )}
          type="button"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : isCurrentPlan ? (
            'Aktueller Plan'
          ) : plan.id === 'free' ? (
            'Kostenlos starten'
          ) : !isAuthenticated ? (
            'Registrieren'
          ) : hasActiveSubscription ? (
            'Wechseln'
          ) : (
            'Auswählen'
          )}
        </button>
      </div>
    </div>
  )
}

function FaqItem({ question, answer }: { question: string; answer: string }) {
  return (
    <div className="card p-6">
      <h3 className="text-base font-medium text-gray-900">{question}</h3>
      <p className="mt-2 text-gray-600">{answer}</p>
    </div>
  )
}

export default Pricing
