import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { Landing } from '@/pages/Landing'
import { Dashboard } from '@/pages/Dashboard'
import { Pricing } from '@/pages/Pricing'
import { Login } from '@/pages/Login'
import { Register } from '@/pages/Register'
import { EmailVerificationPending } from '@/pages/EmailVerificationPending'
import { Impressum } from '@/pages/Impressum'
import { Datenschutz } from '@/pages/Datenschutz'
import { AGB } from '@/pages/AGB'
import { Kontakt } from '@/pages/Kontakt'
import { ValidationDetailPage } from '@/pages/ValidationDetail'
import { DemoCheckout } from '@/pages/DemoCheckout'
import { DemoPortal } from '@/pages/DemoPortal'
import { APIKeysPage } from '@/pages/APIKeys'
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
      </Route>
    </Routes>
  )
}

export default App
