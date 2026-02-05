/**
 * Toast notification utilities using sonner
 * Provides consistent toast notifications across the app
 */

import { toast as sonnerToast } from 'sonner'

export const toast = {
  /**
   * Show a success toast
   */
  success: (message: string, description?: string) => {
    sonnerToast.success(message, { description })
  },

  /**
   * Show an error toast
   */
  error: (message: string, description?: string) => {
    sonnerToast.error(message, { description })
  },

  /**
   * Show a warning toast
   */
  warning: (message: string, description?: string) => {
    sonnerToast.warning(message, { description })
  },

  /**
   * Show an info toast
   */
  info: (message: string, description?: string) => {
    sonnerToast.info(message, { description })
  },

  /**
   * Show a loading toast that can be updated
   */
  loading: (message: string) => {
    return sonnerToast.loading(message)
  },

  /**
   * Show a promise toast (loading → success/error)
   */
  promise: <T>(
    promise: Promise<T>,
    messages: {
      loading: string
      success: string | ((data: T) => string)
      error: string | ((error: unknown) => string)
    }
  ) => {
    return sonnerToast.promise(promise, messages)
  },

  /**
   * Dismiss a toast by ID
   */
  dismiss: (toastId?: string | number) => {
    sonnerToast.dismiss(toastId)
  },
}

// Pre-defined German messages for common actions
export const toastMessages = {
  // Validation
  validationSuccess: 'Validierung erfolgreich',
  validationError: 'Validierung fehlgeschlagen',
  validationWarning: 'Validierung mit Warnungen',

  // File operations
  uploadSuccess: 'Datei erfolgreich hochgeladen',
  uploadError: 'Fehler beim Hochladen',
  downloadSuccess: 'Download gestartet',
  downloadError: 'Download fehlgeschlagen',

  // CRUD operations
  saveSuccess: 'Erfolgreich gespeichert',
  saveError: 'Fehler beim Speichern',
  deleteSuccess: 'Erfolgreich gelöscht',
  deleteError: 'Fehler beim Löschen',
  createSuccess: 'Erfolgreich erstellt',
  createError: 'Fehler beim Erstellen',
  updateSuccess: 'Erfolgreich aktualisiert',
  updateError: 'Fehler beim Aktualisieren',

  // Auth
  loginSuccess: 'Erfolgreich angemeldet',
  loginError: 'Anmeldung fehlgeschlagen',
  logoutSuccess: 'Erfolgreich abgemeldet',
  registerSuccess: 'Registrierung erfolgreich',
  registerError: 'Registrierung fehlgeschlagen',

  // Clipboard
  copiedToClipboard: 'In Zwischenablage kopiert',
  copyError: 'Kopieren fehlgeschlagen',

  // Network
  networkError: 'Netzwerkfehler',
  serverError: 'Serverfehler',
  unauthorized: 'Nicht autorisiert',
} as const
