import { useTranslation } from 'react-i18next'
import { Globe } from 'lucide-react'

const languages = [
  { code: 'de', name: 'Deutsch', flag: 'DE' },
  { code: 'en', name: 'English', flag: 'EN' },
]

export function LanguageSwitcher() {
  const { i18n } = useTranslation()

  const currentLanguage = languages.find((lang) => lang.code === i18n.language) || languages[0]

  const toggleLanguage = () => {
    const nextLang = i18n.language === 'de' ? 'en' : 'de'
    i18n.changeLanguage(nextLang)
  }

  const nextLanguage = i18n.language === 'de' ? 'English' : 'Deutsch'

  return (
    <button
      onClick={toggleLanguage}
      className="flex items-center gap-1.5 px-2 py-1 text-sm text-gray-600 hover:text-gray-900 rounded-md hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
      title={`Switch to ${nextLanguage}`}
      aria-label={`Switch language to ${nextLanguage}`}
    >
      <Globe className="h-4 w-4" aria-hidden="true" />
      <span className="font-medium">{currentLanguage.flag}</span>
    </button>
  )
}
