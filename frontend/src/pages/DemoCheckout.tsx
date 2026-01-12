import { useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { CreditCard, Lock, Loader2, AlertTriangle } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import api from '@/lib/api'
import { cn, formatCurrency } from '@/lib/utils'
import type { PlanTier } from '@/types'

const PLAN_INFO: Record<string, { name: string; priceMonthly: number; priceAnnual: number }> = {
  starter: { name: 'Starter', priceMonthly: 29, priceAnnual: 279 },
  pro: { name: 'Professional', priceMonthly: 79, priceAnnual: 759 },
  steuerberater: { name: 'Steuerberater', priceMonthly: 199, priceAnnual: 1899 },
}

export function DemoCheckout() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [cardNumber, setCardNumber] = useState('4242 4242 4242 4242')
  const [expiry, setExpiry] = useState('12/28')
  const [cvc, setCvc] = useState('123')
  const [name, setName] = useState('Max Mustermann')

  const plan = searchParams.get('plan') as PlanTier || 'starter'
  const annual = searchParams.get('annual') === 'true'
  const successUrl = searchParams.get('success_url') || '/dashboard?checkout=success'

  const planInfo = PLAN_INFO[plan]
  const price = annual ? planInfo?.priceAnnual : planInfo?.priceMonthly
  const period = annual ? 'Jahr' : 'Monat'

  const confirmCheckout = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/billing/demo-confirm?plan=${plan}&annual=${annual}`)
      return response.data
    },
    onSuccess: () => {
      // Redirect to success URL
      const url = new URL(successUrl, window.location.origin)
      navigate(url.pathname + url.search)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    confirmCheckout.mutate()
  }

  if (!planInfo) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="bg-white p-8 rounded-xl shadow-sm text-center">
          <AlertTriangle className="h-12 w-12 text-warning-500 mx-auto mb-4" />
          <h1 className="text-xl font-semibold mb-2">Ungueltiger Plan</h1>
          <p className="text-gray-600">Der angeforderte Plan existiert nicht.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 py-12">
      <div className="max-w-lg mx-auto px-4">
        {/* Demo Banner */}
        <div className="bg-warning-50 border border-warning-200 rounded-lg p-4 mb-6 flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 text-warning-600 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-warning-800">Demo-Modus</p>
            <p className="text-xs text-warning-700">
              Dies ist eine simulierte Checkout-Seite. Keine echte Zahlung wird durchgefuehrt.
            </p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          {/* Header */}
          <div className="bg-primary-600 text-white p-6">
            <h1 className="text-xl font-semibold">Checkout</h1>
            <p className="text-primary-100 text-sm mt-1">
              Abonnement fuer {planInfo.name}
            </p>
          </div>

          {/* Order Summary */}
          <div className="p-6 border-b border-gray-200 bg-gray-50">
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
              Bestelluebersicht
            </h2>
            <div className="flex justify-between items-center">
              <div>
                <p className="font-medium text-gray-900">{planInfo.name} Plan</p>
                <p className="text-sm text-gray-500">
                  {annual ? 'Jaehrliche' : 'Monatliche'} Abrechnung
                </p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(price)}
                </p>
                <p className="text-sm text-gray-500">/{period}</p>
              </div>
            </div>
            {annual && (
              <p className="text-sm text-success-600 mt-2">
                Sie sparen {formatCurrency((planInfo.priceMonthly * 12) - planInfo.priceAnnual)} pro Jahr!
              </p>
            )}
          </div>

          {/* Payment Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
              Zahlungsinformationen
            </h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name auf der Karte
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input w-full"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Kartennummer
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={cardNumber}
                  onChange={(e) => setCardNumber(e.target.value)}
                  className="input w-full pl-10"
                  placeholder="4242 4242 4242 4242"
                  required
                />
                <CreditCard className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Ablaufdatum
                </label>
                <input
                  type="text"
                  value={expiry}
                  onChange={(e) => setExpiry(e.target.value)}
                  className="input w-full"
                  placeholder="MM/JJ"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CVC
                </label>
                <input
                  type="text"
                  value={cvc}
                  onChange={(e) => setCvc(e.target.value)}
                  className="input w-full"
                  placeholder="123"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={confirmCheckout.isPending}
              className={cn(
                'w-full btn-primary py-3 text-lg',
                confirmCheckout.isPending && 'opacity-75'
              )}
            >
              {confirmCheckout.isPending ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin mr-2" />
                  Verarbeitung...
                </>
              ) : (
                <>
                  <Lock className="h-5 w-5 mr-2" />
                  {formatCurrency(price)} bezahlen
                </>
              )}
            </button>

            {confirmCheckout.isError && (
              <div className="p-3 bg-error-50 border border-error-200 rounded-lg text-sm text-error-700">
                Fehler bei der Verarbeitung. Bitte versuchen Sie es erneut.
              </div>
            )}

            <p className="text-xs text-gray-500 text-center flex items-center justify-center gap-1">
              <Lock className="h-3 w-3" />
              Sichere Zahlung - Ihre Daten sind geschuetzt
            </p>
          </form>
        </div>

        {/* Back link */}
        <p className="text-center mt-6">
          <button
            onClick={() => navigate('/preise')}
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Zurueck zur Preisseite
          </button>
        </p>
      </div>
    </div>
  )
}
