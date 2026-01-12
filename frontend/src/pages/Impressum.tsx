import { Mail, Phone, MapPin } from 'lucide-react'

export function Impressum() {
  return (
    <div className="bg-gray-50 min-h-screen py-12">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-xl shadow-sm p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Impressum</h1>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Angaben gemaess § 5 TMG
            </h2>
            <div className="text-gray-600 space-y-2">
              <p className="font-medium text-gray-900">RechnungsChecker GmbH</p>
              <p className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-gray-400" />
                Musterstrasse 123
              </p>
              <p className="pl-6">12345 Berlin</p>
              <p className="pl-6">Deutschland</p>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Kontakt</h2>
            <div className="text-gray-600 space-y-2">
              <p className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-gray-400" />
                +49 (0) 30 123456789
              </p>
              <p className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-gray-400" />
                info@rechnungschecker.de
              </p>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Vertreten durch
            </h2>
            <p className="text-gray-600">
              Geschaeftsfuehrer: Max Mustermann
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Registereintrag
            </h2>
            <div className="text-gray-600 space-y-1">
              <p>Eintragung im Handelsregister</p>
              <p>Registergericht: Amtsgericht Berlin-Charlottenburg</p>
              <p>Registernummer: HRB 123456</p>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Umsatzsteuer-ID
            </h2>
            <p className="text-gray-600">
              Umsatzsteuer-Identifikationsnummer gemaess § 27 a Umsatzsteuergesetz:
              <br />
              DE123456789
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Verantwortlich fuer den Inhalt nach § 55 Abs. 2 RStV
            </h2>
            <div className="text-gray-600">
              <p>Max Mustermann</p>
              <p>Musterstrasse 123</p>
              <p>12345 Berlin</p>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              EU-Streitschlichtung
            </h2>
            <p className="text-gray-600">
              Die Europaeische Kommission stellt eine Plattform zur
              Online-Streitbeilegung (OS) bereit:{' '}
              <a
                href="https://ec.europa.eu/consumers/odr/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:underline"
              >
                https://ec.europa.eu/consumers/odr/
              </a>
              <br />
              Unsere E-Mail-Adresse finden Sie oben im Impressum.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Verbraucherstreitbeilegung/Universalschlichtungsstelle
            </h2>
            <p className="text-gray-600">
              Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren
              vor einer Verbraucherschlichtungsstelle teilzunehmen.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Haftung fuer Inhalte
            </h2>
            <p className="text-gray-600">
              Als Diensteanbieter sind wir gemaess § 7 Abs.1 TMG fuer eigene Inhalte
              auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach
              §§ 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht verpflichtet,
              uebermittelte oder gespeicherte fremde Informationen zu ueberwachen
              oder nach Umstaenden zu forschen, die auf eine rechtswidrige
              Taetigkeit hinweisen.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
