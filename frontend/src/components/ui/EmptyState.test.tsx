import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@/test/test-utils'
import { FileText } from 'lucide-react'
import { EmptyState, emptyStatePresets } from './EmptyState'

describe('EmptyState', () => {
  describe('basic rendering', () => {
    it('renders title and description', () => {
      render(
        <EmptyState
          title="No items found"
          description="There are no items to display."
        />
      )

      expect(screen.getByText('No items found')).toBeInTheDocument()
      expect(screen.getByText('There are no items to display.')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      const { container } = render(
        <EmptyState
          title="Test"
          description="Test description"
          className="custom-class"
        />
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })
  })

  describe('illustrations', () => {
    it('renders documents illustration', () => {
      const { container } = render(
        <EmptyState
          illustration="documents"
          title="No documents"
          description="Upload your first document."
        />
      )

      expect(container.querySelector('svg')).toBeInTheDocument()
    })

    it('renders users illustration', () => {
      const { container } = render(
        <EmptyState
          illustration="users"
          title="No users"
          description="No users found."
        />
      )

      expect(container.querySelector('svg')).toBeInTheDocument()
    })

    it('renders security illustration', () => {
      const { container } = render(
        <EmptyState
          illustration="security"
          title="No keys"
          description="Create an API key."
        />
      )

      expect(container.querySelector('svg')).toBeInTheDocument()
    })

    it('renders analytics illustration', () => {
      const { container } = render(
        <EmptyState
          illustration="analytics"
          title="No data"
          description="No analytics data."
        />
      )

      expect(container.querySelector('svg')).toBeInTheDocument()
    })

    it('renders search illustration', () => {
      const { container } = render(
        <EmptyState
          illustration="search"
          title="No results"
          description="Try different search terms."
        />
      )

      expect(container.querySelector('svg')).toBeInTheDocument()
    })

    it('renders folder illustration', () => {
      const { container } = render(
        <EmptyState
          illustration="folder"
          title="Empty folder"
          description="This folder is empty."
        />
      )

      expect(container.querySelector('svg')).toBeInTheDocument()
    })

    it('renders webhook illustration', () => {
      const { container } = render(
        <EmptyState
          illustration="webhook"
          title="No webhooks"
          description="Configure webhooks."
        />
      )

      expect(container.querySelector('svg')).toBeInTheDocument()
    })
  })

  describe('icon', () => {
    it('renders custom icon when provided', () => {
      const { container } = render(
        <EmptyState
          icon={FileText}
          title="No files"
          description="Upload some files."
        />
      )

      expect(container.querySelector('svg')).toBeInTheDocument()
    })

    it('icon takes precedence when no illustration', () => {
      const { container } = render(
        <EmptyState
          icon={FileText}
          title="Test"
          description="Test"
        />
      )

      // Should have icon wrapper with bg-gray-100
      expect(container.querySelector('.bg-gray-100.rounded-full')).toBeInTheDocument()
    })
  })

  describe('actions', () => {
    it('renders primary action button with onClick', () => {
      const onClick = vi.fn()
      render(
        <EmptyState
          title="Empty"
          description="Nothing here"
          action={{ label: 'Add Item', onClick }}
        />
      )

      const button = screen.getByRole('button', { name: 'Add Item' })
      expect(button).toBeInTheDocument()

      fireEvent.click(button)
      expect(onClick).toHaveBeenCalled()
    })

    it('renders primary action as link with href', () => {
      render(
        <EmptyState
          title="Empty"
          description="Nothing here"
          action={{ label: 'Go to page', href: '/some-page' }}
        />
      )

      const link = screen.getByRole('link', { name: 'Go to page' })
      expect(link).toHaveAttribute('href', '/some-page')
    })

    it('renders secondary action button', () => {
      const onClick = vi.fn()
      render(
        <EmptyState
          title="Empty"
          description="Nothing here"
          action={{ label: 'Primary', onClick: vi.fn() }}
          secondaryAction={{ label: 'Secondary', onClick }}
        />
      )

      const button = screen.getByRole('button', { name: 'Secondary' })
      expect(button).toBeInTheDocument()

      fireEvent.click(button)
      expect(onClick).toHaveBeenCalled()
    })

    it('renders secondary action as link', () => {
      render(
        <EmptyState
          title="Empty"
          description="Nothing here"
          secondaryAction={{ label: 'Learn more', href: '/help' }}
        />
      )

      const link = screen.getByRole('link', { name: 'Learn more' })
      expect(link).toHaveAttribute('href', '/help')
    })
  })

  describe('sizes', () => {
    it('renders small size', () => {
      const { container } = render(
        <EmptyState
          title="Small"
          description="Small size"
          size="sm"
        />
      )

      expect(container.firstChild).toHaveClass('py-8')
    })

    it('renders medium size (default)', () => {
      const { container } = render(
        <EmptyState
          title="Medium"
          description="Medium size"
        />
      )

      expect(container.firstChild).toHaveClass('py-12')
    })

    it('renders large size', () => {
      const { container } = render(
        <EmptyState
          title="Large"
          description="Large size"
          size="lg"
        />
      )

      expect(container.firstChild).toHaveClass('py-16')
    })
  })

  describe('presets', () => {
    it('noValidations preset has correct content', () => {
      expect(emptyStatePresets.noValidations.title).toBe('Keine Validierungen vorhanden')
      expect(emptyStatePresets.noValidations.illustration).toBe('documents')
    })

    it('noSearchResults preset has correct content', () => {
      expect(emptyStatePresets.noSearchResults.title).toBe('Keine Ergebnisse gefunden')
      expect(emptyStatePresets.noSearchResults.illustration).toBe('search')
    })

    it('noClients preset has correct content', () => {
      expect(emptyStatePresets.noClients.title).toBe('Keine Mandanten angelegt')
      expect(emptyStatePresets.noClients.illustration).toBe('users')
    })

    it('noApiKeys preset has correct content', () => {
      expect(emptyStatePresets.noApiKeys.title).toBe('Keine API-Schlüssel vorhanden')
      expect(emptyStatePresets.noApiKeys.illustration).toBe('security')
    })

    it('noTemplates preset has correct content', () => {
      expect(emptyStatePresets.noTemplates.title).toBe('Keine Vorlagen vorhanden')
      expect(emptyStatePresets.noTemplates.illustration).toBe('folder')
    })

    it('noWebhooks preset has correct content', () => {
      expect(emptyStatePresets.noWebhooks.title).toBe('Keine Webhooks konfiguriert')
      expect(emptyStatePresets.noWebhooks.illustration).toBe('webhook')
    })

    it('noAnalytics preset has correct content', () => {
      expect(emptyStatePresets.noAnalytics.title).toBe('Noch keine Daten verfügbar')
      expect(emptyStatePresets.noAnalytics.illustration).toBe('analytics')
    })

    it('can use preset with EmptyState component', () => {
      render(
        <EmptyState
          {...emptyStatePresets.noValidations}
        />
      )

      expect(screen.getByText('Keine Validierungen vorhanden')).toBeInTheDocument()
    })
  })
})
