import { Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { Layout } from '@/components/Layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { AdminRoute } from '@/components/AdminRoute'

// Critical path - keep eager loaded
import { Landing } from '@/pages/Landing'
import { Login } from '@/pages/Login'
import { Register } from '@/pages/Register'

// Lazy loaded pages - Auth
const EmailVerificationPending = lazy(() => import('@/pages/EmailVerificationPending'))
const ForgotPassword = lazy(() => import('@/pages/ForgotPassword'))
const ResetPassword = lazy(() => import('@/pages/ResetPassword'))
const GoogleCallback = lazy(() => import('@/pages/GoogleCallback'))

// Lazy loaded pages - Legal
const Impressum = lazy(() => import('@/pages/Impressum'))
const Datenschutz = lazy(() => import('@/pages/Datenschutz'))
const AGB = lazy(() => import('@/pages/AGB'))
const Kontakt = lazy(() => import('@/pages/Kontakt'))

// Lazy loaded pages - Public
const Pricing = lazy(() => import('@/pages/Pricing'))
const ApiDocs = lazy(() => import('@/pages/ApiDocs'))

// Lazy loaded pages - Dashboard
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const ValidationHistory = lazy(() => import('@/pages/ValidationHistory'))
const ValidationDetailPage = lazy(() => import('@/pages/ValidationDetail'))

// Lazy loaded pages - Settings
const SettingsPage = lazy(() => import('@/pages/Settings'))
const APIKeysPage = lazy(() => import('@/pages/APIKeys'))
const ClientsPage = lazy(() => import('@/pages/Clients'))

// Lazy loaded pages - Features
const ConversionPage = lazy(() => import('@/pages/Conversion'))
const BatchConversionPage = lazy(() => import('@/pages/BatchConversion'))
const InvoiceCreatorPage = lazy(() => import('@/pages/InvoiceCreator'))
const BatchUploadPage = lazy(() => import('@/pages/BatchUpload'))
const AnalyticsPage = lazy(() => import('@/pages/Analytics'))
const TemplatesPage = lazy(() => import('@/pages/Templates'))
const IntegrationsPage = lazy(() => import('@/pages/Integrations'))
const WebhooksPage = lazy(() => import('@/pages/Webhooks'))
const ExportPage = lazy(() => import('@/pages/Export'))
const TeamPage = lazy(() => import('@/pages/Team'))
const ScheduledValidationsPage = lazy(() => import('@/pages/ScheduledValidations'))

// Lazy loaded pages - Demo
const DemoCheckout = lazy(() => import('@/pages/DemoCheckout'))
const DemoPortal = lazy(() => import('@/pages/DemoPortal'))

// Lazy loaded pages - Admin
const AdminDashboard = lazy(() => import('@/pages/admin/AdminDashboard'))
const AdminUsers = lazy(() => import('@/pages/admin/AdminUsers'))

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
    </div>
  )
}

function App() {
  return (
    <Suspense fallback={<PageLoader />}>
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
        <Route path="auth/google/callback" element={<GoogleCallback />} />
        <Route path="impressum" element={<Impressum />} />
        <Route path="datenschutz" element={<Datenschutz />} />
        <Route path="agb" element={<AGB />} />
        <Route path="kontakt" element={<Kontakt />} />
        <Route path="api-dokumentation" element={<ApiDocs />} />
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
        <Route
          path="team"
          element={
            <ProtectedRoute>
              <TeamPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="rechnung-erstellen"
          element={
            <ProtectedRoute>
              <InvoiceCreatorPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="rechnung-erstellen/:draftId"
          element={
            <ProtectedRoute>
              <InvoiceCreatorPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="geplante-validierungen"
          element={
            <ProtectedRoute>
              <ScheduledValidationsPage />
            </ProtectedRoute>
          }
        />
        {/* Admin Routes */}
        <Route
          path="admin"
          element={
            <AdminRoute>
              <AdminDashboard />
            </AdminRoute>
          }
        />
        <Route
          path="admin/users"
          element={
            <AdminRoute>
              <AdminUsers />
            </AdminRoute>
          }
        />
      </Route>
    </Routes>
    </Suspense>
  )
}

export default App
