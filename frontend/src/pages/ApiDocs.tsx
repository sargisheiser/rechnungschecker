import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Key,
  Copy,
  Check,
  ArrowRight,
  Shield,
  Zap,
  Code,
  Terminal,
  CheckCircle,
  AlertTriangle,
  ExternalLink,
} from 'lucide-react'
import { useAuthStore } from '@/hooks/useAuth'

interface CodeBlockProps {
  code: string
  language?: string
  title?: string
}

function CodeBlock({ code, language = 'bash', title }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="rounded-lg overflow-hidden border border-gray-200 my-4">
      {title && (
        <div className="bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 border-b border-gray-200 flex items-center justify-between">
          <span>{title}</span>
          <span className="text-xs text-gray-500">{language}</span>
        </div>
      )}
      <div className="relative">
        <pre className="bg-gray-900 text-gray-100 p-4 overflow-x-auto text-sm">
          <code>{code}</code>
        </pre>
        <button
          onClick={handleCopy}
          className="absolute top-2 right-2 p-2 rounded bg-gray-700 hover:bg-gray-600 transition-colors"
          title="Code kopieren"
        >
          {copied ? (
            <Check className="h-4 w-4 text-green-400" />
          ) : (
            <Copy className="h-4 w-4 text-gray-300" />
          )}
        </button>
      </div>
    </div>
  )
}

interface StepProps {
  number: number
  title: string
  children: React.ReactNode
}

function Step({ number, title, children }: StepProps) {
  return (
    <div className="flex gap-4 mb-8">
      <div className="flex-shrink-0">
        <div className="w-10 h-10 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-bold text-lg">
          {number}
        </div>
      </div>
      <div className="flex-1">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">{title}</h3>
        {children}
      </div>
    </div>
  )
}

export function ApiDocs() {
  const { isAuthenticated } = useAuthStore()

  return (
    <div className="py-12 lg:py-16">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 mb-6">
            <Key className="h-8 w-8 text-primary-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">API Integration Guide</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Lernen Sie, wie Sie RechnungsChecker in Ihre Anwendung integrieren.
            Mit wenigen Schritten koennen Sie E-Rechnungen automatisch validieren.
          </p>
        </div>

        {/* Requirements */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-12">
          <h2 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Voraussetzungen
          </h2>
          <ul className="space-y-2 text-blue-700">
            <li className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 flex-shrink-0" />
              <span><strong>Professional</strong> oder <strong>Steuerberater</strong> Plan</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 flex-shrink-0" />
              <span>Verifiziertes Benutzerkonto</span>
            </li>
          </ul>
          {!isAuthenticated && (
            <div className="mt-4 pt-4 border-t border-blue-200">
              <Link to="/registrieren?plan=pro" className="btn-primary inline-flex items-center gap-2">
                Jetzt upgraden
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          )}
        </div>

        {/* Steps */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-8">So starten Sie</h2>

          <Step number={1} title="API-Schluessel erstellen">
            <p className="text-gray-600 mb-4">
              Gehen Sie zu den Einstellungen und erstellen Sie einen neuen API-Schluessel.
              Geben Sie ihm einen aussagekraeftigen Namen, z.B. "Buchhaltungssoftware" oder "ERP-System".
            </p>
            <Link
              to="/api-keys"
              className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 font-medium"
            >
              <Key className="h-4 w-4" />
              Zu den API-Schluesseln
              <ArrowRight className="h-4 w-4" />
            </Link>

            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex gap-3">
                <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-yellow-800 font-medium">Wichtig</p>
                  <p className="text-yellow-700 text-sm mt-1">
                    Der vollstaendige API-Schluessel wird nur einmal angezeigt.
                    Kopieren Sie ihn sofort und speichern Sie ihn sicher.
                  </p>
                </div>
              </div>
            </div>
          </Step>

          <Step number={2} title="API-Schluessel sicher speichern">
            <p className="text-gray-600 mb-4">
              Speichern Sie den API-Schluessel als Umgebungsvariable.
              Committen Sie ihn <strong>niemals</strong> in Ihr Repository.
            </p>
            <CodeBlock
              title=".env Datei"
              language="env"
              code={`# RechnungsChecker API
RECHNUNGSCHECKER_API_KEY=rck_live_xxxxxxxxxxxxxxxxxxxx`}
            />
            <p className="text-sm text-gray-500 mt-2">
              Fuegen Sie <code className="bg-gray-100 px-1 rounded">.env</code> zu Ihrer <code className="bg-gray-100 px-1 rounded">.gitignore</code> hinzu.
            </p>
          </Step>

          <Step number={3} title="API aufrufen">
            <p className="text-gray-600 mb-4">
              Senden Sie Ihre E-Rechnungen zur Validierung. Der API-Schluessel wird im
              Authorization-Header mitgeschickt.
            </p>

            <div className="space-y-4">
              <CodeBlock
                title="cURL Beispiel"
                language="bash"
                code={`curl -X POST https://api.rechnungschecker.de/v1/validate/ \\
  -H "Authorization: Bearer $RECHNUNGSCHECKER_API_KEY" \\
  -F "file=@rechnung.xml"`}
              />

              <CodeBlock
                title="Python Beispiel"
                language="python"
                code={`import os
import requests

API_KEY = os.environ.get("RECHNUNGSCHECKER_API_KEY")

response = requests.post(
    "https://api.rechnungschecker.de/v1/validate/",
    headers={"Authorization": f"Bearer {API_KEY}"},
    files={"file": open("rechnung.xml", "rb")}
)

result = response.json()
print(f"Gueltig: {result['is_valid']}")
print(f"Fehler: {result['error_count']}")
print(f"Warnungen: {result['warning_count']}")`}
              />

              <CodeBlock
                title="JavaScript/Node.js Beispiel"
                language="javascript"
                code={`const fs = require('fs');
const FormData = require('form-data');
const axios = require('axios');

const API_KEY = process.env.RECHNUNGSCHECKER_API_KEY;

async function validateInvoice(filePath) {
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));

  const response = await axios.post(
    'https://api.rechnungschecker.de/v1/validate/',
    form,
    {
      headers: {
        'Authorization': \`Bearer \${API_KEY}\`,
        ...form.getHeaders()
      }
    }
  );

  console.log('Gueltig:', response.data.is_valid);
  return response.data;
}

validateInvoice('./rechnung.xml');`}
              />

              <CodeBlock
                title="PHP Beispiel"
                language="php"
                code={`<?php
$apiKey = getenv('RECHNUNGSCHECKER_API_KEY');

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, 'https://api.rechnungschecker.de/v1/validate/');
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    "Authorization: Bearer $apiKey"
]);
curl_setopt($ch, CURLOPT_POSTFIELDS, [
    'file' => new CURLFile('rechnung.xml')
]);

$response = curl_exec($ch);
$result = json_decode($response, true);

echo "Gueltig: " . ($result['is_valid'] ? 'Ja' : 'Nein') . "\\n";
echo "Fehler: " . $result['error_count'] . "\\n";`}
              />
            </div>
          </Step>

          <Step number={4} title="Ergebnis verarbeiten">
            <p className="text-gray-600 mb-4">
              Die API gibt ein JSON-Objekt mit dem Validierungsergebnis zurueck.
            </p>
            <CodeBlock
              title="Beispiel-Antwort"
              language="json"
              code={`{
  "id": "val_abc123def456",
  "is_valid": false,
  "file_type": "xrechnung",
  "error_count": 2,
  "warning_count": 1,
  "errors": [
    {
      "code": "BR-CO-25",
      "message": "Summe der Rechnungspositionen stimmt nicht ueberein",
      "location": "/Invoice/LegalMonetaryTotal",
      "severity": "error"
    },
    {
      "code": "BR-16",
      "message": "Rechnungsnummer fehlt",
      "location": "/Invoice/ID",
      "severity": "error"
    }
  ],
  "warnings": [
    {
      "code": "BR-CL-01",
      "message": "Empfohlenes Feld fehlt: Zahlungsbedingungen",
      "location": "/Invoice/PaymentTerms",
      "severity": "warning"
    }
  ],
  "validated_at": "2024-01-15T10:30:00Z"
}`}
            />
          </Step>
        </div>

        {/* API Endpoints Overview */}
        <div className="bg-gray-50 rounded-xl p-6 mb-12">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Terminal className="h-5 w-5" />
            Verfuegbare Endpunkte
          </h2>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 bg-white rounded-lg border border-gray-200">
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-blue-100 text-blue-700">POST</span>
              <div>
                <code className="text-sm font-mono text-gray-800">/v1/validate/</code>
                <p className="text-sm text-gray-600 mt-1">Einzelne Rechnung validieren</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-white rounded-lg border border-gray-200">
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-blue-100 text-blue-700">POST</span>
              <div>
                <code className="text-sm font-mono text-gray-800">/v1/batch/validate</code>
                <p className="text-sm text-gray-600 mt-1">Mehrere Rechnungen gleichzeitig validieren</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-white rounded-lg border border-gray-200">
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-blue-100 text-blue-700">POST</span>
              <div>
                <code className="text-sm font-mono text-gray-800">/v1/convert/</code>
                <p className="text-sm text-gray-600 mt-1">PDF zu XRechnung/ZUGFeRD konvertieren</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-white rounded-lg border border-gray-200">
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-green-100 text-green-700">GET</span>
              <div>
                <code className="text-sm font-mono text-gray-800">/v1/validate/history</code>
                <p className="text-sm text-gray-600 mt-1">Validierungshistorie abrufen</p>
              </div>
            </div>
          </div>

          <p className="text-sm text-gray-500 mt-4">
            Base URL: <code className="bg-gray-200 px-1 rounded">https://api.rechnungschecker.de</code>
          </p>
        </div>

        {/* Tips */}
        <div className="grid md:grid-cols-2 gap-6 mb-12">
          <div className="bg-green-50 border border-green-200 rounded-xl p-6">
            <div className="flex items-center gap-2 text-green-700 font-semibold mb-3">
              <Zap className="h-5 w-5" />
              Best Practices
            </div>
            <ul className="space-y-2 text-green-700 text-sm">
              <li>Verwenden Sie Umgebungsvariablen fuer API-Keys</li>
              <li>Implementieren Sie Retry-Logik fuer Netzwerkfehler</li>
              <li>Cachen Sie Validierungsergebnisse wenn moeglich</li>
              <li>Nutzen Sie Batch-Validierung fuer viele Dateien</li>
            </ul>
          </div>

          <div className="bg-red-50 border border-red-200 rounded-xl p-6">
            <div className="flex items-center gap-2 text-red-700 font-semibold mb-3">
              <AlertTriangle className="h-5 w-5" />
              Vermeiden Sie
            </div>
            <ul className="space-y-2 text-red-700 text-sm">
              <li>API-Keys im Quellcode speichern</li>
              <li>Keys in oeffentlichen Repos committen</li>
              <li>Einen Key fuer mehrere Anwendungen nutzen</li>
              <li>Unverschluesselte HTTP-Verbindungen</li>
            </ul>
          </div>
        </div>

        {/* Rate Limits */}
        <div className="bg-gray-100 rounded-xl p-6 mb-12">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Rate Limits</h2>
          <p className="text-gray-600 mb-4">
            Die API-Nutzung ist je nach Plan begrenzt. Ueberschreiten Sie das Limit,
            erhalten Sie einen <code className="bg-gray-200 px-1 rounded">429 Too Many Requests</code> Fehler.
          </p>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-left text-sm text-gray-500">
                  <th className="pb-2">Plan</th>
                  <th className="pb-2">API-Aufrufe/Monat</th>
                  <th className="pb-2">Requests/Minute</th>
                </tr>
              </thead>
              <tbody className="text-gray-700">
                <tr className="border-t border-gray-200">
                  <td className="py-2 font-medium">Professional</td>
                  <td className="py-2">10.000</td>
                  <td className="py-2">60</td>
                </tr>
                <tr className="border-t border-gray-200">
                  <td className="py-2 font-medium">Steuerberater</td>
                  <td className="py-2">100.000</td>
                  <td className="py-2">120</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Help */}
        <div className="text-center">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Brauchen Sie Hilfe?</h2>
          <p className="text-gray-600 mb-6">
            Unser Support-Team hilft Ihnen gerne bei der Integration.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/kontakt"
              className="btn-primary inline-flex items-center justify-center gap-2"
            >
              <Code className="h-4 w-4" />
              Support kontaktieren
            </Link>
            <a
              href="https://api.rechnungschecker.de/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary inline-flex items-center justify-center gap-2"
            >
              <ExternalLink className="h-4 w-4" />
              OpenAPI Dokumentation
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ApiDocs
