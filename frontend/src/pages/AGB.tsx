export function AGB() {
  return (
    <div className="bg-gray-50 min-h-screen py-12">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-xl shadow-sm p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">
            Allgemeine Geschaeftsbedingungen (AGB)
          </h1>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              § 1 Geltungsbereich
            </h2>
            <p className="text-gray-600 mb-4">
              (1) Diese Allgemeinen Geschaeftsbedingungen (AGB) gelten fuer alle
              Vertraege zwischen der RechnungsChecker GmbH (nachfolgend "Anbieter")
              und dem Nutzer (nachfolgend "Kunde") ueber die Nutzung der
              RechnungsChecker-Plattform zur Validierung und Konvertierung von
              E-Rechnungen.
            </p>
            <p className="text-gray-600">
              (2) Abweichende Bedingungen des Kunden werden nicht anerkannt, es sei
              denn, der Anbieter stimmt ihrer Geltung ausdruecklich schriftlich zu.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              § 2 Vertragsgegenstand
            </h2>
            <p className="text-gray-600 mb-4">
              (1) Der Anbieter stellt dem Kunden eine webbasierte Plattform zur
              Verfuegung, mit der E-Rechnungen im Format XRechnung und ZUGFeRD
              validiert werden koennen.
            </p>
            <p className="text-gray-600 mb-4">
              (2) Die Leistungen umfassen je nach gewahltem Tarif:
            </p>
            <ul className="list-disc list-inside text-gray-600 mb-4 space-y-1">
              <li>Validierung von XRechnung-Dateien (XML)</li>
              <li>Validierung von ZUGFeRD-Rechnungen (PDF)</li>
              <li>Erstellung von PDF-Validierungsberichten</li>
              <li>API-Zugang fuer automatisierte Validierungen</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              § 3 Vertragsschluss und Registrierung
            </h2>
            <p className="text-gray-600 mb-4">
              (1) Die Nutzung der kostenpflichtigen Dienste setzt eine Registrierung
              voraus. Mit der Registrierung gibt der Kunde ein Angebot auf Abschluss
              eines Nutzungsvertrages ab.
            </p>
            <p className="text-gray-600 mb-4">
              (2) Der Kunde ist verpflichtet, bei der Registrierung wahrheitsgemaesse
              Angaben zu machen und diese aktuell zu halten.
            </p>
            <p className="text-gray-600">
              (3) Der Vertrag kommt mit der Bestaetigung der Registrierung durch den
              Anbieter zustande.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              § 4 Preise und Zahlung
            </h2>
            <p className="text-gray-600 mb-4">
              (1) Es gelten die zum Zeitpunkt des Vertragsschlusses gueltigen Preise
              gemaess der aktuellen Preisliste auf der Website.
            </p>
            <p className="text-gray-600 mb-4">
              (2) Alle Preise verstehen sich zzgl. der gesetzlichen Mehrwertsteuer.
            </p>
            <p className="text-gray-600 mb-4">
              (3) Die Zahlung erfolgt per Kreditkarte oder SEPA-Lastschrift ueber
              unseren Zahlungsdienstleister Stripe.
            </p>
            <p className="text-gray-600">
              (4) Bei Abonnements wird der Betrag monatlich oder jaehrlich im Voraus
              abgebucht.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              § 5 Kostenlose Nutzung
            </h2>
            <p className="text-gray-600 mb-4">
              (1) Nicht registrierte Nutzer (Gaeste) koennen eine Validierung
              kostenlos durchfuehren.
            </p>
            <p className="text-gray-600">
              (2) Registrierte Nutzer im kostenlosen Tarif erhalten ein begrenztes
              Kontingent an Validierungen pro Monat gemaess der aktuellen
              Tarifuebersicht.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              § 6 Verfuegbarkeit und Gewaehrleistung
            </h2>
            <p className="text-gray-600 mb-4">
              (1) Der Anbieter bemuecht sich um eine Verfuegbarkeit der Plattform von
              99% im Jahresmittel. Hiervon ausgenommen sind Zeiten, in denen die
              Server aufgrund von technischen Problemen, die nicht im
              Einflussbereich des Anbieters liegen, nicht erreichbar sind.
            </p>
            <p className="text-gray-600">
              (2) Die Validierungsergebnisse basieren auf den offiziellen Pruefregeln
              des KoSIT. Der Anbieter uebernimmt keine Garantie fuer die
              Vollstaendigkeit oder Richtigkeit der Ergebnisse.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              § 7 Haftung
            </h2>
            <p className="text-gray-600 mb-4">
              (1) Der Anbieter haftet unbeschraenkt fuer Vorsatz und grobe
              Fahrlaessigkeit.
            </p>
            <p className="text-gray-600 mb-4">
              (2) Bei leichter Fahrlaessigkeit haftet der Anbieter nur bei Verletzung
              wesentlicher Vertragspflichten (Kardinalpflichten). Die Haftung ist in
              diesem Fall auf den vorhersehbaren, vertragstypischen Schaden begrenzt.
            </p>
            <p className="text-gray-600">
              (3) Die Haftung fuer Schaeden aus der Verletzung des Lebens, des
              Koerpers oder der Gesundheit bleibt unberuehrt.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              § 8 Kuendigung
            </h2>
            <p className="text-gray-600 mb-4">
              (1) Der Kunde kann kostenpflichtige Abonnements jederzeit zum Ende der
              jeweiligen Abrechnungsperiode kuendigen.
            </p>
            <p className="text-gray-600 mb-4">
              (2) Die Kuendigung kann ueber das Kundenportal oder per E-Mail an
              support@rechnungschecker.de erfolgen.
            </p>
            <p className="text-gray-600">
              (3) Das Recht zur ausserordentlichen Kuendigung aus wichtigem Grund
              bleibt unberuehrt.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              § 9 Datenschutz
            </h2>
            <p className="text-gray-600">
              Die Erhebung und Verarbeitung personenbezogener Daten erfolgt gemaess
              unserer Datenschutzerklaerung. Hochgeladene Rechnungsdaten werden
              ausschliesslich zur Validierung verarbeitet und nach maximal 30
              Minuten automatisch geloescht.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              § 10 Schlussbestimmungen
            </h2>
            <p className="text-gray-600 mb-4">
              (1) Es gilt das Recht der Bundesrepublik Deutschland unter Ausschluss
              des UN-Kaufrechts.
            </p>
            <p className="text-gray-600 mb-4">
              (2) Gerichtsstand fuer alle Streitigkeiten aus diesem Vertrag ist
              Berlin, sofern der Kunde Kaufmann, juristische Person des oeffentlichen
              Rechts oder oeffentlich-rechtliches Sondervermoegen ist.
            </p>
            <p className="text-gray-600">
              (3) Sollten einzelne Bestimmungen dieser AGB unwirksam sein, bleibt die
              Wirksamkeit der uebrigen Bestimmungen unberuehrt.
            </p>
          </section>

          <p className="text-gray-500 text-sm mt-8">Stand: Januar 2024</p>
        </div>
      </div>
    </div>
  )
}
