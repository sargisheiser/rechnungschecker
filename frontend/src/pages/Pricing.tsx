import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Check, X, Loader2, AlertCircle } from 'lucide-react'
import { usePlans, useCheckout } from '@/hooks/useBilling'
import { useAuthStore } from '@/hooks/useAuth'
import { cn, formatCurrency } from '@/lib/utils'
import type { Plan, PlanTier } from '@/types'

export function Pricing() {
  const [annual, setAnnual] = useState(true)
  const [searchParams] = useSearchParams()
  const { data: plans, isLoading } = usePlans()
  const { isAuthenticated } = useAuthStore()
  const checkout = useCheckout()

  const checkoutCanceled = searchParams.get('checkout') === 'canceled'

  const handleSelectPlan = (planId: PlanTier) => {
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

    checkout.mutate({ plan: planId, annual })
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
            Waehlen Sie den passenden Plan fuer Ihr Unternehmen. Keine
            versteckten Kosten.
          </p>

          {checkoutCanceled && (
            <div className="mt-6 p-4 bg-warning-50 border border-warning-200 rounded-lg inline-flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-warning-600" />
              <span className="text-warning-700">
                Checkout abgebrochen. Sie koennen jederzeit erneut starten.
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
        </div>

        {/* Plans */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans?.map((plan) => (
              <PlanCard
                key={plan.id}
                plan={plan}
                annual={annual}
                onSelect={() => handleSelectPlan(plan.id)}
                isLoading={checkout.isPending}
                isAuthenticated={isAuthenticated}
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
              answer="Ja, Sie koennen jederzeit upgraden oder downgraden. Bei einem Upgrade wird der Preisunterschied anteilig berechnet."
            />
            <FaqItem
              question="Gibt es eine Kuendigungsfrist?"
              answer="Nein, Sie koennen Ihr Abonnement jederzeit kuendigen. Es laeuft dann zum Ende der aktuellen Abrechnungsperiode aus."
            />
            <FaqItem
              question="Was passiert mit meinen Daten nach der Kuendigung?"
              answer="Ihre Validierungshistorie bleibt 30 Tage nach Kuendigung erhalten. Danach werden alle Daten geloescht."
            />
            <FaqItem
              question="Bieten Sie Rabatte fuer groessere Teams?"
              answer="Ja, fuer Unternehmen mit mehr als 10 Nutzern bieten wir individuelle Konditionen. Kontaktieren Sie uns."
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
}: {
  plan: Plan
  annual: boolean
  onSelect: () => void
  isLoading: boolean
  isAuthenticated: boolean
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
        'card flex flex-col',
        plan.popular && 'ring-2 ring-primary-500 relative'
      )}
    >
      {plan.popular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
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
            {formatCurrency(monthlyEquivalent)}
          </span>
          <span className="text-gray-500">/Monat</span>
          {annual && price > 0 && (
            <p className="text-sm text-gray-500 mt-1">
              {formatCurrency(price)} jaehrlich
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

      <div className="p-6 pt-0">
        <button
          onClick={onSelect}
          disabled={isLoading}
          className={cn(
            'w-full',
            plan.popular ? 'btn-primary' : 'btn-secondary'
          )}
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : plan.id === 'free' ? (
            'Kostenlos starten'
          ) : !isAuthenticated ? (
            'Registrieren'
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
