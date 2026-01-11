import { Link } from 'react-router-dom'
import {
  FileCheck,
  Shield,
  Zap,
  Clock,
  CheckCircle,
  ArrowRight,
  Building2,
  Users,
} from 'lucide-react'
import { FileUpload } from '@/components/FileUpload'
import { ValidationResults } from '@/components/ValidationResults'
import { useValidationStore } from '@/hooks/useValidation'

export function Landing() {
  const { currentResult } = useValidationStore()

  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-b from-primary-50 to-white py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 text-balance">
              E-Rechnungen validieren in{' '}
              <span className="text-primary-600">Sekunden</span>
            </h1>
            <p className="mt-6 text-lg md:text-xl text-gray-600 text-balance">
              Pruefen Sie Ihre XRechnung und ZUGFeRD Dateien sofort auf
              Konformitaet. Kostenlos und ohne Registrierung.
            </p>

            {/* Upload Area */}
            <div className="mt-10 max-w-2xl mx-auto">
              {currentResult ? (
                <ValidationResults />
              ) : (
                <FileUpload />
              )}
            </div>

            {/* Trust badges */}
            <div className="mt-8 flex flex-wrap justify-center gap-6 text-sm text-gray-500">
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-success-500" />
                DSGVO-konform
              </div>
              <div className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-warning-500" />
                Sofortige Ergebnisse
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-primary-500" />
                24/7 verfuegbar
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
              Alles was Sie brauchen
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Umfassende E-Rechnungspruefung fuer deutsche Unternehmen
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard
              icon={FileCheck}
              title="XRechnung Validierung"
              description="Vollstaendige Pruefung nach XRechnung Standard 3.0 mit detaillierten Fehlermeldungen auf Deutsch."
            />
            <FeatureCard
              icon={FileCheck}
              title="ZUGFeRD Unterstuetzung"
              description="Validierung von ZUGFeRD 2.0, 2.1 und Factur-X Profilen von MINIMUM bis EXTENDED."
            />
            <FeatureCard
              icon={Shield}
              title="Datenschutz"
              description="Ihre Rechnungsdaten werden niemals gespeichert. Verarbeitung erfolgt DSGVO-konform in Deutschland."
            />
            <FeatureCard
              icon={Zap}
              title="Schnelle Ergebnisse"
              description="Erhalten Sie Validierungsergebnisse in wenigen Sekunden mit klaren, verstaendlichen Fehlerbeschreibungen."
            />
            <FeatureCard
              icon={Building2}
              title="API-Zugang"
              description="Integrieren Sie die Validierung direkt in Ihre Systeme mit unserer REST-API (Pro-Plan)."
            />
            <FeatureCard
              icon={Users}
              title="Mandantenverwaltung"
              description="Verwalten Sie mehrere Mandanten in einem Account - ideal fuer Steuerberater."
            />
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-16 lg:py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
              So funktioniert's
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <StepCard
              number="1"
              title="Datei hochladen"
              description="Laden Sie Ihre XRechnung (XML) oder ZUGFeRD (PDF) Datei hoch."
            />
            <StepCard
              number="2"
              title="Automatische Pruefung"
              description="Unsere Engine prueft alle Regeln des deutschen E-Rechnungsstandards."
            />
            <StepCard
              number="3"
              title="Ergebnis erhalten"
              description="Sie erhalten sofort eine detaillierte Auswertung mit Handlungsempfehlungen."
            />
          </div>
        </div>
      </section>

      {/* Standards Section */}
      <section className="py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
              Unterstuetzte Standards
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Vollstaendige Abdeckung aller relevanten deutschen E-Rechnungsformate
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="card p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                XRechnung
              </h3>
              <ul className="space-y-3">
                <CheckItem text="XRechnung Standard 2.3 und 3.0" />
                <CheckItem text="UBL und CII Syntax" />
                <CheckItem text="EN 16931 konform" />
                <CheckItem text="Leitweg-ID Validierung" />
              </ul>
            </div>
            <div className="card p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                ZUGFeRD / Factur-X
              </h3>
              <ul className="space-y-3">
                <CheckItem text="ZUGFeRD 2.0, 2.1, 2.2" />
                <CheckItem text="Factur-X 1.0" />
                <CheckItem text="Alle Profile: MINIMUM bis EXTENDED" />
                <CheckItem text="Automatische Profilerkennung" />
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 lg:py-24 bg-primary-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white">
            Bereit Ihre E-Rechnungen zu pruefen?
          </h2>
          <p className="mt-4 text-lg text-primary-100">
            Starten Sie jetzt kostenlos - keine Kreditkarte erforderlich.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/registrieren"
              className="btn btn-lg bg-white text-primary-600 hover:bg-gray-100"
            >
              Kostenlos registrieren
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
            <Link
              to="/preise"
              className="btn btn-lg bg-primary-700 text-white hover:bg-primary-800"
            >
              Preise ansehen
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}

function FeatureCard({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof FileCheck
  title: string
  description: string
}) {
  return (
    <div className="card-hover p-6">
      <div className="w-12 h-12 rounded-lg bg-primary-100 flex items-center justify-center mb-4">
        <Icon className="h-6 w-6 text-primary-600" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

function StepCard({
  number,
  title,
  description,
}: {
  number: string
  title: string
  description: string
}) {
  return (
    <div className="text-center">
      <div className="w-12 h-12 rounded-full bg-primary-600 text-white text-xl font-bold flex items-center justify-center mx-auto mb-4">
        {number}
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

function CheckItem({ text }: { text: string }) {
  return (
    <li className="flex items-center gap-2">
      <CheckCircle className="h-5 w-5 text-success-500 flex-shrink-0" />
      <span className="text-gray-700">{text}</span>
    </li>
  )
}
