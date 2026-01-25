import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { Landing } from '@/pages/Landing'
import { Dashboard } from '@/pages/Dashboard'
import { Pricing } from '@/pages/Pricing'
import { Login } from '@/pages/Login'
import { Register } from '@/pages/Register'
import { EmailVerificationPending } from '@/pages/EmailVerificationPending'
import { ForgotPassword } from '@/pages/ForgotPassword'
import { ResetPassword } from '@/pages/ResetPassword'
import { Impressum } from '@/pages/Impressum'
import { Datenschutz } from '@/pages/Datenschutz'
import { AGB } from '@/pages/AGB'
import { Kontakt } from '@/pages/Kontakt'
import { ValidationDetailPage } from '@/pages/ValidationDetail'
import { DemoCheckout } from '@/pages/DemoCheckout'
import { DemoPortal } from '@/pages/DemoPortal'
import { APIKeysPage } from '@/pages/APIKeys'
import { ClientsPage } from '@/pages/Clients'
import { ConversionPage } from '@/pages/Conversion'
import { IntegrationsPage } from '@/pages/Integrations'
import { WebhooksPage } from '@/pages/Webhooks'
import { ExportPage } from '@/pages/Export'
import { SettingsPage } from '@/pages/Settings'
import AnalyticsPage from '@/pages/Analytics'
import BatchUploadPage from '@/pages/BatchUpload'
import BatchConversionPage from '@/pages/BatchConversion'
import { TemplatesPage } from '@/pages/Templates'
import { ValidationHistory } from '@/pages/ValidationHistory'
import { ProtectedRoute } from '@/components/ProtectedRoute'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Landing />} />
        <Route path="preise" element={<Pricing />} />
        <Route path="login" element={<Login />} />
        <Route path="registrieren" element={<Register />} />
        <Route path="email-bestaetigung" element={<EmailVerificationPending />} />
        <Route path="passwort-vergessen" element={<ForgotPassword />} />
        <Route path="passwort-zuruecksetzen" element={<ResetPassword />} />
        <Route path="verifizieren" element={<Navigate to="/email-bestaetigung" replace />} />
        <Route path="impressum" element={<Impressum />} />
        <Route path="datenschutz" element={<Datenschutz />} />
        <Route path="agb" element={<AGB />} />
        <Route path="kontakt" element={<Kontakt />} />
        <Route
          path="demo-checkout"
          element={
            <ProtectedRoute>
              <DemoCheckout />
            </ProtectedRoute>
          }
        />
        <Route
          path="demo-portal"
          element={
            <ProtectedRoute>
              <DemoPortal />
            </ProtectedRoute>
          }
        />
        <Route
          path="dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="dashboard/verlauf"
          element={
            <ProtectedRoute>
              <ValidationHistory />
            </ProtectedRoute>
          }
        />
        <Route
          path="validierung/:id"
          element={
            <ProtectedRoute>
              <ValidationDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="api-keys"
          element={
            <ProtectedRoute>
              <APIKeysPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="mandanten"
          element={
            <ProtectedRoute>
              <ClientsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="konvertierung"
          element={
            <ProtectedRoute>
              <ConversionPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="batch-konvertierung"
          element={
            <ProtectedRoute>
              <BatchConversionPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="integrationen"
          element={
            <ProtectedRoute>
              <IntegrationsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="webhooks"
          element={
            <ProtectedRoute>
              <WebhooksPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="export"
          element={
            <ProtectedRoute>
              <ExportPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="einstellungen"
          element={
            <ProtectedRoute>
              <SettingsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="analytik"
          element={
            <ProtectedRoute>
              <AnalyticsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="batch"
          element={
            <ProtectedRoute>
              <BatchUploadPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="vorlagen"
          element={
            <ProtectedRoute>
              <TemplatesPage />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  )
}

export default App
