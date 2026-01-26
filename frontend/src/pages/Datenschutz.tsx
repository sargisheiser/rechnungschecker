export function Datenschutz() {
  return (
    <div className="bg-gray-50 min-h-screen py-12">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-xl shadow-sm p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">
            Datenschutzerklaerung
          </h1>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              1. Datenschutz auf einen Blick
            </h2>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Allgemeine Hinweise
            </h3>
            <p className="text-gray-600 mb-4">
              Die folgenden Hinweise geben einen einfachen Ueberblick darueber, was
              mit Ihren personenbezogenen Daten passiert, wenn Sie diese Website
              besuchen. Personenbezogene Daten sind alle Daten, mit denen Sie
              persönlich identifiziert werden können.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              2. Verantwortliche Stelle
            </h2>
            <div className="text-gray-600 space-y-2">
              <p>RechnungsChecker GmbH</p>
              <p>Musterstrasse 123</p>
              <p>12345 Berlin</p>
              <p>E-Mail: datenschutz@rechnungschecker.de</p>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              3. Datenerfassung auf dieser Website
            </h2>

            <h3 className="text-lg font-medium text-gray-900 mb-2 mt-4">
              Cookies
            </h3>
            <p className="text-gray-600 mb-4">
              Unsere Website verwendet Cookies. Das sind kleine Textdateien, die Ihr
              Webbrowser auf Ihrem Endgeraet speichert. Cookies helfen uns dabei,
              unser Angebot nutzerfreundlicher und sicherer zu machen.
            </p>

            <h3 className="text-lg font-medium text-gray-900 mb-2 mt-4">
              Server-Log-Dateien
            </h3>
            <p className="text-gray-600 mb-4">
              Der Provider der Seiten erhebt und speichert automatisch Informationen
              in so genannten Server-Log-Dateien, die Ihr Browser automatisch an uns
              uebermittelt. Dies sind:
            </p>
            <ul className="list-disc list-inside text-gray-600 mb-4 space-y-1">
              <li>Browsertyp und Browserversion</li>
              <li>Verwendetes Betriebssystem</li>
              <li>Referrer URL</li>
              <li>Hostname des zugreifenden Rechners</li>
              <li>Uhrzeit der Serveranfrage</li>
              <li>IP-Adresse</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              4. Registrierung und Nutzerkonto
            </h2>
            <p className="text-gray-600 mb-4">
              Sie können sich auf unserer Website registrieren, um zusätzliche
              Funktionen nutzen zu können. Die dabei eingegebenen Daten verwenden
              wir nur zum Zwecke der Nutzung des jeweiligen Angebotes oder Dienstes,
              für den Sie sich registriert haben.
            </p>
            <p className="text-gray-600 mb-4">
              Bei der Registrierung erfassen wir:
            </p>
            <ul className="list-disc list-inside text-gray-600 mb-4 space-y-1">
              <li>E-Mail-Adresse</li>
              <li>Passwort (verschluesselt gespeichert)</li>
              <li>Zeitpunkt der Registrierung</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              5. Verarbeitung von Rechnungsdaten
            </h2>
            <p className="text-gray-600 mb-4">
              Wenn Sie eine Rechnung zur Validierung hochladen, wird diese
              voruebergehend auf unseren Servern verarbeitet. Die Rechnungsdaten
              werden:
            </p>
            <ul className="list-disc list-inside text-gray-600 mb-4 space-y-1">
              <li>Ausschliesslich zur Validierung verwendet</li>
              <li>Nach maximal 30 Minuten automatisch geloescht</li>
              <li>Nicht an Dritte weitergegeben</li>
              <li>Verschluesselt uebertragen (TLS/SSL)</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              6. Zahlungsabwicklung
            </h2>
            <p className="text-gray-600 mb-4">
              Für die Zahlungsabwicklung nutzen wir den Dienst Stripe. Bei
              Bezahlvorgaengen werden Ihre Zahlungsdaten direkt an Stripe
              uebermittelt und dort verarbeitet. Wir speichern keine
              Kreditkartendaten auf unseren Servern.
            </p>
            <p className="text-gray-600">
              Weitere Informationen finden Sie in der Datenschutzerklaerung von
              Stripe:{' '}
              <a
                href="https://stripe.com/de/privacy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:underline"
              >
                https://stripe.com/de/privacy
              </a>
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              7. Ihre Rechte
            </h2>
            <p className="text-gray-600 mb-4">Sie haben jederzeit das Recht:</p>
            <ul className="list-disc list-inside text-gray-600 mb-4 space-y-1">
              <li>
                Auskunft ueber Ihre bei uns gespeicherten Daten zu erhalten
              </li>
              <li>Berichtigung unrichtiger Daten zu verlangen</li>
              <li>Loeschung Ihrer Daten zu verlangen</li>
              <li>
                Einschraenkung der Verarbeitung Ihrer Daten zu verlangen
              </li>
              <li>Der Verarbeitung Ihrer Daten zu widersprechen</li>
              <li>Datenuebertragbarkeit zu verlangen</li>
            </ul>
            <p className="text-gray-600">
              Wenden Sie sich hierzu an: datenschutz@rechnungschecker.de
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              8. Datensicherheit
            </h2>
            <p className="text-gray-600">
              Wir verwenden innerhalb des Website-Besuchs das verbreitete
              SSL-Verfahren (Secure Socket Layer) in Verbindung mit der jeweils
              hoechsten Verschluesselungsstufe, die von Ihrem Browser unterstuetzt
              wird. Alle Daten werden verschluesselt uebertragen und in sicheren
              Rechenzentren in Deutschland gespeichert.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              9. Änderungen dieser Datenschutzerklaerung
            </h2>
            <p className="text-gray-600">
              Wir behalten uns vor, diese Datenschutzerklaerung anzupassen, damit
              sie stets den aktuellen rechtlichen Anforderungen entspricht oder um
              Änderungen unserer Leistungen umzusetzen. Für Ihren erneuten Besuch
              gilt dann die neue Datenschutzerklaerung.
            </p>
            <p className="text-gray-500 text-sm mt-4">
              Stand: Januar 2024
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
