import { useState } from 'react'
import { Mail, Phone, MapPin, Send, Clock } from 'lucide-react'

export function Kontakt() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
  })
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Create mailto link with form data
    const subjectMap: Record<string, string> = {
      general: 'Allgemeine Anfrage',
      technical: 'Technische Frage',
      billing: 'Fragen zur Abrechnung',
      partnership: 'Partnerschaft / Kooperation',
      feedback: 'Feedback / Verbesserungsvorschlag',
      other: 'Sonstiges',
    }

    const emailSubject = `[RechnungsChecker] ${subjectMap[formData.subject] || formData.subject}`
    const emailBody = `Name: ${formData.name}\nE-Mail: ${formData.email}\n\nNachricht:\n${formData.message}`

    // Open email client with pre-filled data
    window.location.href = `mailto:support@rechnungschecker.de?subject=${encodeURIComponent(emailSubject)}&body=${encodeURIComponent(emailBody)}`

    setSubmitted(true)
  }

  return (
    <div className="bg-gray-50 min-h-screen py-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Kontaktieren Sie uns
          </h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Haben Sie Fragen zu RechnungsChecker? Wir helfen Ihnen gerne weiter.
            Schreiben Sie uns eine Nachricht oder nutzen Sie unsere Kontaktdaten.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Contact Info */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Kontaktinformationen
              </h2>

              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <Mail className="h-5 w-5 text-primary-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">E-Mail</p>
                    <a
                      href="mailto:support@rechnungschecker.de"
                      className="text-sm text-primary-600 hover:underline"
                    >
                      support@rechnungschecker.de
                    </a>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Phone className="h-5 w-5 text-primary-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Telefon</p>
                    <a
                      href="tel:+493012345678"
                      className="text-sm text-gray-600"
                    >
                      +49 (0) 30 123456789
                    </a>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <MapPin className="h-5 w-5 text-primary-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Adresse</p>
                    <p className="text-sm text-gray-600">
                      RechnungsChecker GmbH
                      <br />
                      Musterstrasse 123
                      <br />
                      12345 Berlin
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Clock className="h-5 w-5 text-primary-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Geschaeftszeiten
                    </p>
                    <p className="text-sm text-gray-600">
                      Mo - Fr: 9:00 - 17:00 Uhr
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-primary-50 rounded-xl p-6">
              <h3 className="text-sm font-semibold text-primary-900 mb-2">
                Technischer Support
              </h3>
              <p className="text-sm text-primary-700">
                Für technische Fragen zur API oder Integration wenden Sie sich an{' '}
                <a
                  href="mailto:technik@rechnungschecker.de"
                  className="underline"
                >
                  technik@rechnungschecker.de
                </a>
              </p>
            </div>
          </div>

          {/* Contact Form */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">
                Nachricht senden
              </h2>

              {submitted ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-success-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Send className="h-8 w-8 text-success-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Nachricht gesendet!
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Vielen Dank für Ihre Nachricht. Wir werden uns innerhalb von
                    24 Stunden bei Ihnen melden.
                  </p>
                  <button
                    onClick={() => {
                      setSubmitted(false)
                      setFormData({ name: '', email: '', subject: '', message: '' })
                    }}
                    className="btn-secondary"
                  >
                    Neue Nachricht
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label
                        htmlFor="name"
                        className="block text-sm font-medium text-gray-700 mb-1"
                      >
                        Name *
                      </label>
                      <input
                        type="text"
                        id="name"
                        required
                        className="input"
                        value={formData.name}
                        onChange={(e) =>
                          setFormData({ ...formData, name: e.target.value })
                        }
                      />
                    </div>
                    <div>
                      <label
                        htmlFor="email"
                        className="block text-sm font-medium text-gray-700 mb-1"
                      >
                        E-Mail *
                      </label>
                      <input
                        type="email"
                        id="email"
                        required
                        className="input"
                        value={formData.email}
                        onChange={(e) =>
                          setFormData({ ...formData, email: e.target.value })
                        }
                      />
                    </div>
                  </div>

                  <div>
                    <label
                      htmlFor="subject"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Betreff *
                    </label>
                    <select
                      id="subject"
                      required
                      className="input"
                      value={formData.subject}
                      onChange={(e) =>
                        setFormData({ ...formData, subject: e.target.value })
                      }
                    >
                      <option value="">Bitte wählen...</option>
                      <option value="general">Allgemeine Anfrage</option>
                      <option value="technical">Technische Frage</option>
                      <option value="billing">Fragen zur Abrechnung</option>
                      <option value="partnership">Partnerschaft / Kooperation</option>
                      <option value="feedback">Feedback / Verbesserungsvorschlag</option>
                      <option value="other">Sonstiges</option>
                    </select>
                  </div>

                  <div>
                    <label
                      htmlFor="message"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Nachricht *
                    </label>
                    <textarea
                      id="message"
                      required
                      rows={6}
                      className="input"
                      value={formData.message}
                      onChange={(e) =>
                        setFormData({ ...formData, message: e.target.value })
                      }
                    />
                  </div>

                  <div className="flex items-start gap-2">
                    <input
                      type="checkbox"
                      id="privacy"
                      required
                      className="mt-1"
                    />
                    <label htmlFor="privacy" className="text-sm text-gray-600">
                      Ich habe die{' '}
                      <a href="/datenschutz" className="text-primary-600 hover:underline">
                        Datenschutzerklaerung
                      </a>{' '}
                      gelesen und bin mit der Verarbeitung meiner Daten
                      einverstanden. *
                    </label>
                  </div>

                  <button type="submit" className="btn-primary w-full sm:w-auto">
                    <Send className="h-4 w-4 mr-2" />
                    Nachricht senden
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
