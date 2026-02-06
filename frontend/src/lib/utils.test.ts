import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  cn,
  formatDate,
  formatDateTime,
  formatCurrency,
  formatFileSize,
  getFileExtension,
  isValidInvoiceFile,
  generateGuestId,
  getGuestId,
} from './utils'

describe('cn (classname utility)', () => {
  it('merges class names correctly', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('handles conditional classes', () => {
    expect(cn('base', false && 'hidden', true && 'visible')).toBe('base visible')
  })

  it('merges tailwind classes correctly', () => {
    expect(cn('px-2 py-1', 'px-4')).toBe('py-1 px-4')
  })

  it('handles arrays', () => {
    expect(cn(['foo', 'bar'])).toBe('foo bar')
  })

  it('handles undefined and null', () => {
    expect(cn('foo', undefined, null, 'bar')).toBe('foo bar')
  })
})

describe('formatDate', () => {
  it('formats date string correctly', () => {
    const result = formatDate('2024-01-15')
    expect(result).toBe('15.01.2024')
  })

  it('formats Date object correctly', () => {
    const date = new Date(2024, 0, 15) // Month is 0-indexed
    const result = formatDate(date)
    expect(result).toBe('15.01.2024')
  })

  it('handles different date formats', () => {
    const result = formatDate('2024-12-31T23:59:59Z')
    expect(result).toMatch(/\d{2}\.\d{2}\.\d{4}/)
  })
})

describe('formatDateTime', () => {
  it('formats datetime with time component', () => {
    // Use a fixed date to avoid timezone issues
    const date = new Date('2024-01-15T14:30:00')
    const result = formatDateTime(date)
    expect(result).toMatch(/15\.01\.2024/)
    expect(result).toMatch(/\d{2}:\d{2}/)
  })

  it('formats ISO string correctly', () => {
    const result = formatDateTime('2024-06-20T09:15:00Z')
    expect(result).toMatch(/\d{2}\.\d{2}\.\d{4}, \d{2}:\d{2}/)
  })
})

describe('formatCurrency', () => {
  it('formats positive amount correctly', () => {
    const result = formatCurrency(1234.56)
    expect(result).toMatch(/1\.234,56/)
    expect(result).toMatch(/€/)
  })

  it('formats zero correctly', () => {
    const result = formatCurrency(0)
    expect(result).toMatch(/0,00/)
  })

  it('formats negative amount correctly', () => {
    const result = formatCurrency(-500)
    expect(result).toMatch(/-500,00/)
  })

  it('formats large numbers correctly', () => {
    const result = formatCurrency(1000000)
    expect(result).toMatch(/1\.000\.000,00/)
  })
})

describe('formatFileSize', () => {
  it('formats bytes correctly', () => {
    expect(formatFileSize(500)).toBe('500 B')
  })

  it('formats kilobytes correctly', () => {
    expect(formatFileSize(1024)).toBe('1 KB')
    expect(formatFileSize(1536)).toBe('1.5 KB')
  })

  it('formats megabytes correctly', () => {
    expect(formatFileSize(1048576)).toBe('1 MB')
    expect(formatFileSize(5242880)).toBe('5 MB')
  })

  it('formats gigabytes correctly', () => {
    expect(formatFileSize(1073741824)).toBe('1 GB')
  })

  it('handles zero bytes', () => {
    expect(formatFileSize(0)).toBe('0 B')
  })
})

describe('getFileExtension', () => {
  it('extracts extension from filename', () => {
    expect(getFileExtension('document.pdf')).toBe('pdf')
    expect(getFileExtension('invoice.xml')).toBe('xml')
  })

  it('returns lowercase extension', () => {
    expect(getFileExtension('Document.PDF')).toBe('pdf')
    expect(getFileExtension('INVOICE.XML')).toBe('xml')
  })

  it('handles multiple dots in filename', () => {
    expect(getFileExtension('my.invoice.2024.xml')).toBe('xml')
  })

  it('handles no extension', () => {
    expect(getFileExtension('noextension')).toBe('')
  })

  it('handles hidden files (returns empty for dotfiles without extension)', () => {
    // The function treats .gitignore as a file with no extension
    expect(getFileExtension('.gitignore')).toBe('')
  })
})

describe('isValidInvoiceFile', () => {
  it('accepts XML files', () => {
    expect(isValidInvoiceFile('invoice.xml')).toBe(true)
    expect(isValidInvoiceFile('INVOICE.XML')).toBe(true)
  })

  it('accepts PDF files', () => {
    expect(isValidInvoiceFile('invoice.pdf')).toBe(true)
    expect(isValidInvoiceFile('INVOICE.PDF')).toBe(true)
  })

  it('rejects other file types', () => {
    expect(isValidInvoiceFile('document.docx')).toBe(false)
    expect(isValidInvoiceFile('image.png')).toBe(false)
    expect(isValidInvoiceFile('data.json')).toBe(false)
    expect(isValidInvoiceFile('script.js')).toBe(false)
  })

  it('rejects files without extension', () => {
    expect(isValidInvoiceFile('noextension')).toBe(false)
  })
})

describe('generateGuestId', () => {
  it('generates unique IDs', () => {
    const id1 = generateGuestId()
    const id2 = generateGuestId()
    expect(id1).not.toBe(id2)
  })

  it('starts with guest_ prefix', () => {
    const id = generateGuestId()
    expect(id.startsWith('guest_')).toBe(true)
  })

  it('contains timestamp', () => {
    const before = Date.now()
    const id = generateGuestId()
    const after = Date.now()

    const timestamp = parseInt(id.split('_')[1])
    expect(timestamp).toBeGreaterThanOrEqual(before)
    expect(timestamp).toBeLessThanOrEqual(after)
  })
})

describe('getGuestId', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('creates new guest ID if none exists', () => {
    const id = getGuestId()
    expect(id.startsWith('guest_')).toBe(true)
    expect(localStorage.getItem('guest_id')).toBe(id)
  })

  it('returns existing guest ID if present', () => {
    const existingId = 'guest_existing_123'
    localStorage.setItem('guest_id', existingId)

    const id = getGuestId()
    expect(id).toBe(existingId)
  })

  it('persists generated ID', () => {
    const id1 = getGuestId()
    const id2 = getGuestId()
    expect(id1).toBe(id2)
  })
})
