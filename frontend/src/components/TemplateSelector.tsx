import { useState } from 'react'
import { ChevronDown, Check, Plus, Star } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useTemplates } from '@/hooks/useTemplates'
import { cn } from '@/lib/utils'
import type { TemplateType, TemplateListItem } from '@/types'

interface TemplateSelectorProps {
  type: TemplateType
  onSelect: (template: TemplateListItem) => void
  selectedId?: string | null
}

export function TemplateSelector({ type, onSelect, selectedId }: TemplateSelectorProps) {
  const { data: templatesData, isLoading } = useTemplates(type)
  const [isOpen, setIsOpen] = useState(false)

  const templates = templatesData?.items || []
  const selectedTemplate = templates.find((t) => t.id === selectedId)

  if (isLoading) {
    return (
      <div className="animate-pulse h-9 bg-gray-100 rounded-lg w-full"></div>
    )
  }

  if (templates.length === 0) {
    return (
      <Link
        to="/vorlagen"
        className="flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700"
      >
        <Plus className="h-4 w-4" />
        {type === 'sender' ? 'Absender-Vorlage erstellen' : 'Empfaenger-Vorlage erstellen'}
      </Link>
    )
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'w-full flex items-center justify-between gap-2 px-3 py-2 text-sm border rounded-lg transition-colors',
          isOpen
            ? 'border-primary-500 ring-1 ring-primary-500'
            : 'border-gray-300 hover:border-gray-400'
        )}
      >
        <span className={cn(
          'truncate',
          selectedTemplate ? 'text-gray-900' : 'text-gray-500'
        )}>
          {selectedTemplate ? selectedTemplate.name : 'Vorlage waehlen...'}
        </span>
        <ChevronDown className={cn(
          'h-4 w-4 text-gray-400 transition-transform flex-shrink-0',
          isOpen && 'rotate-180'
        )} />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto">
            {/* Clear selection option */}
            <button
              onClick={() => {
                onSelect(null as unknown as TemplateListItem)
                setIsOpen(false)
              }}
              className="w-full px-3 py-2 text-left text-sm text-gray-500 hover:bg-gray-50"
            >
              Keine Vorlage
            </button>
            <hr className="border-gray-100" />

            {templates.map((template) => (
              <button
                key={template.id}
                onClick={() => {
                  onSelect(template)
                  setIsOpen(false)
                }}
                className={cn(
                  'w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center justify-between gap-2',
                  selectedId === template.id && 'bg-primary-50'
                )}
              >
                <div className="flex items-center gap-2 truncate">
                  {template.is_default && (
                    <Star className="h-3 w-3 text-primary-500 fill-current flex-shrink-0" />
                  )}
                  <span className="truncate">{template.name}</span>
                  {template.city && (
                    <span className="text-gray-400 text-xs truncate">({template.city})</span>
                  )}
                </div>
                {selectedId === template.id && (
                  <Check className="h-4 w-4 text-primary-500 flex-shrink-0" />
                )}
              </button>
            ))}

            <hr className="border-gray-100" />
            <Link
              to="/vorlagen"
              onClick={() => setIsOpen(false)}
              className="w-full px-3 py-2 text-left text-sm text-primary-600 hover:bg-primary-50 flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Vorlagen verwalten
            </Link>
          </div>
        </>
      )}
    </div>
  )
}
