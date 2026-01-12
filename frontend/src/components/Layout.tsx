import { Outlet, Link, useNavigate } from 'react-router-dom'
import { FileCheck, Menu, X, User, LogOut } from 'lucide-react'
import { useState } from 'react'
import { useAuthStore, useLogout } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'

export function Layout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { user, isAuthenticated } = useAuthStore()
  const logout = useLogout()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout.mutate()
    navigate('/')
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Logo */}
            <div className="flex items-center">
              <Link to="/" className="flex items-center gap-2">
                <FileCheck className="h-8 w-8 text-primary-600" />
                <span className="text-xl font-bold text-gray-900">
                  RechnungsChecker
                </span>
              </Link>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-6">
              <Link
                to="/"
                className="text-gray-600 hover:text-gray-900 font-medium"
              >
                Startseite
              </Link>
              <Link
                to="/preise"
                className="text-gray-600 hover:text-gray-900 font-medium"
              >
                Preise
              </Link>

              {isAuthenticated ? (
                <div className="flex items-center gap-4">
                  <Link to="/dashboard" className="btn-secondary">
                    Dashboard
                  </Link>
                  <div className="relative group">
                    <button className="flex items-center gap-2 text-gray-600 hover:text-gray-900">
                      <User className="h-5 w-5" />
                      <span className="text-sm">{user?.email}</span>
                    </button>
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      >
                        <LogOut className="h-4 w-4" />
                        Abmelden
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <Link to="/login" className="btn-ghost">
                    Anmelden
                  </Link>
                  <Link to="/registrieren" className="btn-primary">
                    Kostenlos starten
                  </Link>
                </div>
              )}
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden flex items-center">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="text-gray-600 hover:text-gray-900"
              >
                {mobileMenuOpen ? (
                  <X className="h-6 w-6" />
                ) : (
                  <Menu className="h-6 w-6" />
                )}
              </button>
            </div>
          </div>

          {/* Mobile Navigation */}
          <div
            className={cn(
              'md:hidden',
              mobileMenuOpen ? 'block' : 'hidden'
            )}
          >
            <div className="px-2 pt-2 pb-3 space-y-1">
              <Link
                to="/"
                className="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                onClick={() => setMobileMenuOpen(false)}
              >
                Startseite
              </Link>
              <Link
                to="/preise"
                className="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                onClick={() => setMobileMenuOpen(false)}
              >
                Preise
              </Link>
              {isAuthenticated ? (
                <>
                  <Link
                    to="/dashboard"
                    className="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Dashboard
                  </Link>
                  <button
                    onClick={() => {
                      handleLogout()
                      setMobileMenuOpen(false)
                    }}
                    className="block w-full text-left px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                  >
                    Abmelden
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Anmelden
                  </Link>
                  <Link
                    to="/registrieren"
                    className="block px-3 py-2 rounded-lg bg-primary-600 text-white text-center"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Kostenlos starten
                  </Link>
                </>
              )}
            </div>
          </div>
        </nav>
      </header>

      {/* Main content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <FileCheck className="h-6 w-6 text-primary-400" />
                <span className="text-lg font-bold text-white">
                  RechnungsChecker
                </span>
              </div>
              <p className="text-sm max-w-md">
                Die einfachste Loesung zur Validierung und Konvertierung von
                E-Rechnungen nach deutschen Standards. XRechnung und ZUGFeRD
                konform.
              </p>
            </div>
            <div>
              <h3 className="text-white font-semibold mb-4">Produkt</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link to="/" className="hover:text-white">
                    Funktionen
                  </Link>
                </li>
                <li>
                  <Link to="/preise" className="hover:text-white">
                    Preise
                  </Link>
                </li>
                <li>
                  <a href="#" className="hover:text-white">
                    API Dokumentation
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="text-white font-semibold mb-4">Rechtliches</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link to="/impressum" className="hover:text-white">
                    Impressum
                  </Link>
                </li>
                <li>
                  <Link to="/datenschutz" className="hover:text-white">
                    Datenschutz
                  </Link>
                </li>
                <li>
                  <Link to="/agb" className="hover:text-white">
                    AGB
                  </Link>
                </li>
                <li>
                  <Link to="/kontakt" className="hover:text-white">
                    Kontakt
                  </Link>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-sm text-center">
            <p>&copy; {new Date().getFullYear()} RechnungsChecker. Alle Rechte vorbehalten.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
