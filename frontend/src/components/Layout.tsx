import { Outlet, Link, useNavigate } from 'react-router-dom'
import { FileCheck, Menu, X, User, LogOut, Settings, BarChart3, FolderUp, BookTemplate, Shield, LayoutDashboard, FileOutput, Home, CreditCard } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore, useLogout } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'
import { LanguageSwitcher } from './LanguageSwitcher'

export function Layout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { user, isAuthenticated } = useAuthStore()
  const logout = useLogout()
  const navigate = useNavigate()
  const { t } = useTranslation()

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
            <div className="hidden md:flex items-center gap-4">
              <Link
                to="/"
                className="text-gray-600 hover:text-gray-900 font-medium flex items-center gap-1.5"
              >
                <Home className="h-4 w-4" />
                {t('nav.home')}
              </Link>
              <Link
                to="/preise"
                className="text-gray-600 hover:text-gray-900 font-medium flex items-center gap-1.5"
              >
                <CreditCard className="h-4 w-4" />
                {t('nav.pricing')}
              </Link>

              {isAuthenticated ? (
                <div className="flex items-center gap-4">
                  <Link
                    to="/dashboard"
                    className="text-gray-600 hover:text-gray-900 font-medium flex items-center gap-1.5"
                  >
                    <LayoutDashboard className="h-4 w-4" />
                    {t('nav.dashboard')}
                  </Link>
                  <Link
                    to="/konvertierung"
                    className="text-gray-600 hover:text-gray-900 font-medium flex items-center gap-1.5"
                  >
                    <FileOutput className="h-4 w-4" />
                    {t('nav.conversion')}
                  </Link>
                  <Link
                    to="/batch"
                    className="text-gray-600 hover:text-gray-900 font-medium flex items-center gap-1.5"
                  >
                    <FolderUp className="h-4 w-4" />
                    {t('nav.batch')}
                  </Link>
                  <Link
                    to="/analytik"
                    className="text-gray-600 hover:text-gray-900 font-medium flex items-center gap-1.5"
                  >
                    <BarChart3 className="h-4 w-4" />
                    {t('nav.analytics')}
                  </Link>
                  <div className="relative group">
                    <button
                      className="flex items-center gap-2 p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                      aria-label={t('nav.userMenu')}
                      aria-haspopup="menu"
                    >
                      <User className="h-5 w-5" />
                    </button>
                    <div
                      className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all"
                      role="menu"
                      aria-label={t('nav.userMenu')}
                    >
                      {user?.is_admin && (
                        <>
                          <Link
                            to="/admin"
                            className="flex items-center gap-2 px-4 py-2 text-sm text-primary-600 hover:bg-primary-50"
                          >
                            <Shield className="h-4 w-4" />
                            {t('nav.admin')}
                          </Link>
                          <hr className="my-1 border-gray-200" />
                        </>
                      )}
                      <Link
                        to="/vorlagen"
                        className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      >
                        <BookTemplate className="h-4 w-4" />
                        Vorlagen
                      </Link>
                      <Link
                        to="/einstellungen"
                        className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      >
                        <Settings className="h-4 w-4" />
                        {t('nav.settings')}
                      </Link>
                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      >
                        <LogOut className="h-4 w-4" />
                        {t('nav.logout')}
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <Link to="/login" className="btn-ghost">
                    {t('nav.login')}
                  </Link>
                  <Link to="/registrieren" className="btn-primary">
                    {t('nav.getStarted')}
                  </Link>
                </div>
              )}
              <LanguageSwitcher />
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden flex items-center">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-lg p-1"
                aria-label={mobileMenuOpen ? t('nav.closeMenu') : t('nav.openMenu')}
                aria-expanded={mobileMenuOpen}
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
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                onClick={() => setMobileMenuOpen(false)}
              >
                <Home className="h-4 w-4" />
                {t('nav.home')}
              </Link>
              <Link
                to="/preise"
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                onClick={() => setMobileMenuOpen(false)}
              >
                <CreditCard className="h-4 w-4" />
                {t('nav.pricing')}
              </Link>
              {isAuthenticated ? (
                <>
                  <Link
                    to="/dashboard"
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <LayoutDashboard className="h-4 w-4" />
                    {t('nav.dashboard')}
                  </Link>
                  <Link
                    to="/konvertierung"
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <FileOutput className="h-4 w-4" />
                    {t('nav.conversion')}
                  </Link>
                  <Link
                    to="/batch"
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <FolderUp className="h-4 w-4" />
                    {t('nav.batch')}
                  </Link>
                  <Link
                    to="/analytik"
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <BarChart3 className="h-4 w-4" />
                    {t('nav.analytics')}
                  </Link>
                  <Link
                    to="/vorlagen"
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <BookTemplate className="h-4 w-4" />
                    Vorlagen
                  </Link>
                  {user?.is_admin && (
                    <Link
                      to="/admin"
                      className="flex items-center gap-2 px-3 py-2 rounded-lg text-primary-600 hover:bg-primary-50 font-medium"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Shield className="h-4 w-4" />
                      {t('nav.admin')}
                    </Link>
                  )}
                  <Link
                    to="/einstellungen"
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <Settings className="h-4 w-4" />
                    {t('nav.settings')}
                  </Link>
                  <button
                    onClick={() => {
                      handleLogout()
                      setMobileMenuOpen(false)
                    }}
                    className="flex items-center gap-2 w-full text-left px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                  >
                    <LogOut className="h-4 w-4" />
                    {t('nav.logout')}
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {t('nav.login')}
                  </Link>
                  <Link
                    to="/registrieren"
                    className="block px-3 py-2 rounded-lg bg-primary-600 text-white text-center"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {t('nav.getStarted')}
                  </Link>
                </>
              )}
              <div className="px-3 py-2">
                <LanguageSwitcher />
              </div>
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
                {t('footer.description')}
              </p>
            </div>
            <div>
              <h3 className="text-white font-semibold mb-4">{t('footer.product')}</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link to="/" className="hover:text-white">
                    {t('footer.features')}
                  </Link>
                </li>
                <li>
                  <Link to="/preise" className="hover:text-white">
                    {t('nav.pricing')}
                  </Link>
                </li>
                <li>
                  <Link to="/api-dokumentation" className="hover:text-white">
                    {t('footer.apiDocs')}
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="text-white font-semibold mb-4">{t('footer.legal')}</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link to="/impressum" className="hover:text-white">
                    {t('footer.imprint')}
                  </Link>
                </li>
                <li>
                  <Link to="/datenschutz" className="hover:text-white">
                    {t('footer.privacy')}
                  </Link>
                </li>
                <li>
                  <Link to="/agb" className="hover:text-white">
                    {t('footer.terms')}
                  </Link>
                </li>
                <li>
                  <Link to="/kontakt" className="hover:text-white">
                    {t('footer.contact')}
                  </Link>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-sm text-center">
            <p>&copy; {new Date().getFullYear()} RechnungsChecker. {t('footer.allRights')}</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
