// User types
export interface User {
  id: string
  email: string
  company_name?: string
  plan: PlanTier
  is_active: boolean
  created_at: string
}

export type PlanTier = 'free' | 'starter' | 'pro' | 'steuerberater'

// Auth types
export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  company_name?: string
}

// Validation types
export type FileType = 'xrechnung' | 'zugferd' | 'unknown'
export type ValidationStatus = 'valid' | 'invalid' | 'error'
export type ZugferdProfile = 'MINIMUM' | 'BASIC' | 'BASIC_WL' | 'EN16931' | 'EXTENDED' | 'XRECHNUNG'

export interface ValidationError {
  code: string
  message: string
  location?: string
  severity: 'error' | 'warning' | 'info'
}

export interface ValidationResult {
  id: string
  status: ValidationStatus
  file_type: FileType
  file_name: string
  zugferd_profile?: ZugferdProfile
  errors: ValidationError[]
  warnings: ValidationError[]
  validated_at: string
  can_download_report: boolean
}

export interface ValidationHistory {
  items: ValidationResult[]
  total: number
  page: number
  pages: number
}

// Plan types
export interface PlanFeatures {
  validations_per_month: number | null
  conversions_per_month: number
  batch_upload: boolean
  api_access: boolean
  api_calls_per_month: number
  report_download: boolean
  multi_client: boolean
  max_clients: number
  support_level: 'community' | 'email' | 'priority' | 'phone'
}

export interface Plan {
  id: PlanTier
  name: string
  description: string
  price_monthly: number
  price_annual: number
  features: PlanFeatures
  popular?: boolean
}

// Usage types
export interface UsageStats {
  validations_used: number
  validations_limit: number | null
  conversions_used: number
  conversions_limit: number
  period_start: string
  period_end: string
}

// Subscription types
export interface Subscription {
  id: string
  plan: PlanTier
  status: 'active' | 'canceled' | 'past_due' | 'trialing'
  current_period_start: string
  current_period_end: string
  cancel_at_period_end: boolean
}

// API Response types
export interface ApiError {
  detail: string
  code?: string
}
