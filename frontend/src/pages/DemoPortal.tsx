import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  CreditCard,
  AlertTriangle,
  ArrowLeft,
  Loader2,
  Calendar,
  Shield,
} from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useUser } from '@/hooks/useAuth'
import { useSubscription } from '@/hooks/useBilling'
import { formatCurrency, formatDate } from '@/lib/utils'

const PLAN_INFO: Record<string, { name: string; priceMonthly: number }> = {
  free: { name: 'Kostenlos', priceMonthly: 0 },
  starter: { name: 'Starter', priceMonthly: 29 },
  pro: { name: 'Professional', priceMonthly: 79 },
  steuerberater: { name: 'Steuerberater', priceMonthly: 199 },
}

export function DemoPortal() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: user } = useUser()
  const { data: subscription } = useSubscription()
  const [showConfirm, setShowConfirm] = useState(false)

  const cancelSubscription = useMutation({
    mutationFn: async () => {
      const response = await api.post('/billing/demo-cancel')
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user'] })
      queryClient.invalidateQueries({ queryKey: ['subscription'] })
      queryClient.invalidateQueries({ queryKey: ['usage'] })
      navigate('/dashboard')
    },
  })

  const planInfo = PLAN_INFO[user?.plan || 'free']

  return (
    <div className="min-h-screen bg-gray-100 py-12">
      <div className="max-w-2xl mx-auto px-4">
        {/* Demo Banner */}
        <div className="bg-warning-50 border border-warning-200 rounded-lg p-4 mb-6 flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 text-warning-600 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-warning-800">Demo-Modus</p>
            <p className="text-xs text-warning-700">
              Dies ist ein simuliertes Kundenportal. Keine echten Zahlungen werden verarbeitet.
            </p>
          </div>
        </div>

        {/* Back Link */}
        <Link
          to="/dashboard"
          className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Zurück zum Dashboard
        </Link>

        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          {/* Header */}
          <div className="bg-primary-600 text-white p-6">
            <h1 className="text-xl font-semibold">Abo-Verwaltung</h1>
            <p className="text-primary-100 text-sm mt-1">
              Verwalten Sie Ihr RechnungsChecker-Abonnement
            </p>
          </div>

          {/* Current Plan */}
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
              Aktueller Plan
            </h2>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <Shield className="h-6 w-6 text-primary-600" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900 text-lg">
                    {planInfo?.name}
                  </p>
                  <p className="text-sm text-gray-500">
                    {planInfo?.priceMonthly === 0
                      ? 'Kostenlos'
                      : `${formatCurrency(planInfo?.priceMonthly || 0)}/Monat`}
                  </p>
                </div>
              </div>
              {user?.plan !== 'free' && (
                <span className="px-3 py-1 bg-success-100 text-success-700 text-sm font-medium rounded-full">
                  Aktiv
                </span>
              )}
            </div>

            {subscription?.current_period_end && (
              <div className="mt-4 flex items-center gap-2 text-sm text-gray-600">
                <Calendar className="h-4 w-4" />
                <span>
                  Naechste Abrechnung: {formatDate(subscription.current_period_end)}
                </span>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="p-6 space-y-4">
            {user?.plan === 'free' ? (
              <div className="text-center py-4">
                <p className="text-gray-600 mb-4">
                  Sie nutzen derzeit den kostenlosen Plan.
                </p>
                <Link to="/preise" className="btn-primary">
                  Upgrade auf einen bezahlten Plan
                </Link>
              </div>
            ) : (
              <>
                {/* Change Plan */}
                <div className="p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">Plan ändern</p>
                      <p className="text-sm text-gray-500">
                        Wechseln Sie zu einem anderen Plan
                      </p>
                    </div>
                    <Link to="/preise" className="btn-secondary btn-sm">
                      Plaene ansehen
                    </Link>
                  </div>
                </div>

                {/* Payment Method */}
                <div className="p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <CreditCard className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="font-medium text-gray-900">Zahlungsmethode</p>
                        <p className="text-sm text-gray-500">
                          **** **** **** 4242 (Demo)
                        </p>
                      </div>
                    </div>
                    <button className="btn-ghost btn-sm" disabled>
                      Ändern
                    </button>
                  </div>
                </div>

                {/* Cancel Subscription */}
                {!showConfirm ? (
                  <button
                    onClick={() => setShowConfirm(true)}
                    className="w-full text-center text-sm text-error-600 hover:text-error-700 py-2"
                  >
                    Abonnement kuendigen
                  </button>
                ) : (
                  <div className="p-4 bg-error-50 border border-error-200 rounded-lg">
                    <p className="text-sm text-error-700 mb-4">
                      Sind Sie sicher, dass Sie Ihr Abonnement kuendigen moechten?
                      Sie werden auf den kostenlosen Plan zurueckgestuft.
                    </p>
                    <div className="flex gap-3">
                      <button
                        onClick={() => cancelSubscription.mutate()}
                        disabled={cancelSubscription.isPending}
                        className="btn-primary bg-error-600 hover:bg-error-700"
                      >
                        {cancelSubscription.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        ) : null}
                        Ja, kuendigen
                      </button>
                      <button
                        onClick={() => setShowConfirm(false)}
                        className="btn-secondary"
                      >
                        Abbrechen
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Billing History */}
          <div className="p-6 border-t border-gray-200 bg-gray-50">
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
              Rechnungsverlauf
            </h2>
            <div className="text-center py-4 text-sm text-gray-500">
              <p>Keine Rechnungen vorhanden (Demo-Modus)</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
