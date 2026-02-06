import { useState, useRef, useEffect, useCallback } from 'react'
import { Pencil, Check, X, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface InlineEditProps {
  /** Current value */
  value: string
  /** Called when value is saved */
  onSave: (value: string) => Promise<void> | void
  /** Placeholder text when empty */
  placeholder?: string
  /** Whether editing is disabled */
  disabled?: boolean
  /** Input type */
  type?: 'text' | 'textarea'
  /** Max length for input */
  maxLength?: number
  /** Custom class name for the display text */
  className?: string
  /** Custom class name for the input */
  inputClassName?: string
  /** Number of rows for textarea */
  rows?: number
  /** Show edit icon on hover */
  showEditIcon?: boolean
  /** Text to show when value is empty */
  emptyText?: string
}

export function InlineEdit({
  value,
  onSave,
  placeholder = 'Klicken zum Bearbeiten',
  disabled = false,
  type = 'text',
  maxLength,
  className,
  inputClassName,
  rows = 3,
  showEditIcon = true,
  emptyText = 'Nicht angegeben',
}: InlineEditProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(value)
  const [isSaving, setIsSaving] = useState(false)
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null)

  // Update edit value when prop changes
  useEffect(() => {
    if (!isEditing) {
      setEditValue(value)
    }
  }, [value, isEditing])

  // Focus input when entering edit mode
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      // Move cursor to end
      if (inputRef.current instanceof HTMLInputElement) {
        inputRef.current.selectionStart = inputRef.current.value.length
      }
    }
  }, [isEditing])

  const handleSave = useCallback(async () => {
    const trimmedValue = editValue.trim()

    // Skip if value hasn't changed
    if (trimmedValue === value) {
      setIsEditing(false)
      return
    }

    try {
      setIsSaving(true)
      await onSave(trimmedValue)
      setIsEditing(false)
    } catch (error) {
      // Keep editing on error
      console.error('Failed to save:', error)
    } finally {
      setIsSaving(false)
    }
  }, [editValue, value, onSave])

  const handleCancel = useCallback(() => {
    setEditValue(value)
    setIsEditing(false)
  }, [value])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && type === 'text') {
        e.preventDefault()
        handleSave()
      } else if (e.key === 'Enter' && e.metaKey && type === 'textarea') {
        e.preventDefault()
        handleSave()
      } else if (e.key === 'Escape') {
        e.preventDefault()
        handleCancel()
      }
    },
    [handleSave, handleCancel, type]
  )

  if (isEditing) {
    const InputComponent = type === 'textarea' ? 'textarea' : 'input'

    return (
      <div className="relative group">
        <InputComponent
          ref={inputRef as React.RefObject<HTMLInputElement & HTMLTextAreaElement>}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleSave}
          disabled={isSaving}
          maxLength={maxLength}
          rows={type === 'textarea' ? rows : undefined}
          placeholder={placeholder}
          className={cn(
            'w-full px-3 py-2 text-sm border border-primary-300 rounded-lg',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'bg-white',
            isSaving && 'opacity-50',
            inputClassName
          )}
        />

        {/* Action buttons */}
        <div className="absolute right-2 top-2 flex items-center gap-1">
          {isSaving ? (
            <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
          ) : (
            <>
              <button
                type="button"
                onClick={handleSave}
                className="p-1 text-success-600 hover:bg-success-50 rounded transition-colors"
                title="Speichern (Enter)"
              >
                <Check className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={handleCancel}
                className="p-1 text-gray-400 hover:bg-gray-100 rounded transition-colors"
                title="Abbrechen (Esc)"
              >
                <X className="h-4 w-4" />
              </button>
            </>
          )}
        </div>

        {/* Helper text for textarea */}
        {type === 'textarea' && (
          <p className="mt-1 text-xs text-gray-400">
            ⌘+Enter zum Speichern, Esc zum Abbrechen
          </p>
        )}
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={() => !disabled && setIsEditing(true)}
      disabled={disabled}
      className={cn(
        'group relative w-full text-left transition-colors rounded-lg',
        !disabled && 'hover:bg-gray-50 cursor-pointer',
        disabled && 'cursor-not-allowed opacity-60',
        className
      )}
    >
      <span
        className={cn(
          'block py-1',
          !value && 'text-gray-400 italic'
        )}
      >
        {value || emptyText}
      </span>

      {/* Edit icon */}
      {showEditIcon && !disabled && (
        <span className="absolute right-0 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
          <Pencil className="h-4 w-4 text-gray-400" />
        </span>
      )}
    </button>
  )
}

// Simplified inline edit for single-line fields in tables/lists
interface InlineEditSimpleProps {
  value: string
  onSave: (value: string) => Promise<void> | void
  className?: string
  placeholder?: string
}

export function InlineEditSimple({
  value,
  onSave,
  className,
  placeholder = 'Bearbeiten...',
}: InlineEditSimpleProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(value)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  const handleSave = async () => {
    if (editValue.trim() !== value) {
      await onSave(editValue.trim())
    }
    setIsEditing(false)
  }

  if (isEditing) {
    return (
      <input
        ref={inputRef}
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        onBlur={handleSave}
        onKeyDown={(e) => {
          if (e.key === 'Enter') handleSave()
          if (e.key === 'Escape') {
            setEditValue(value)
            setIsEditing(false)
          }
        }}
        className={cn(
          'px-2 py-1 text-sm border border-primary-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500',
          className
        )}
        placeholder={placeholder}
      />
    )
  }

  return (
    <span
      onClick={() => setIsEditing(true)}
      className={cn(
        'cursor-pointer hover:bg-gray-100 px-2 py-1 -mx-2 rounded transition-colors',
        !value && 'text-gray-400 italic',
        className
      )}
    >
      {value || placeholder}
    </span>
  )
}
