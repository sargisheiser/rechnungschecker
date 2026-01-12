// User types
export interface User {
  id: string
  email: string
  company_name?: string
  plan: PlanTier
  is_active: boolean
  is_verified: boolean
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

// Backend response format
export interface ValidationApiResponse {
  id: string
  is_valid: boolean
  file_type: string
  file_hash: string
  error_count: number
  warning_count: number
  info_count: number
  errors: Array<{
    severity: string
    code: string
    message_de: string
    message_en?: string
    location?: string
    suggestion?: string
  }>
  warnings: Array<{
    severity: string
    code: string
    message_de: string
    message_en?: string
    location?: string
    suggestion?: string
  }>
  infos: Array<{
    severity: string
    code: string
    message_de: string
    message_en?: string
    location?: string
    suggestion?: string
  }>
  xrechnung_version?: string
  zugferd_profile?: string
  validator_version: string
  processing_time_ms: number
  validated_at: string
  report_url?: string
  // Guest-specific fields
  guest_id?: string
  validations_used?: number
  validations_limit?: number
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
  // Guest-specific fields
  guest_id?: string
  validations_used?: number
  validations_limit?: number
}

export interface ValidationHistoryItem {
  id: string
  file_name?: string
  file_type: FileType
  is_valid: boolean
  error_count: number
  warning_count: number
  validated_at: string
}

export interface ValidationHistory {
  items: ValidationHistoryItem[]
  total: number
  page: number
  page_size: number
}

export interface ValidationDetail {
  id: string
  file_name?: string
  file_type: FileType
  file_hash: string
  is_valid: boolean
  error_count: number
  warning_count: number
  info_count: number
  xrechnung_version?: string
  zugferd_profile?: string
  processing_time_ms: number
  validator_version: string
  notes?: string
  validated_at: string
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

// API Key types
export interface APIKey {
  id: string
  name: string
  description?: string
  key_prefix: string
  is_active: boolean
  created_at: string
  expires_at?: string
  last_used_at?: string
  usage_count: number
  requests_this_month: number
}

export interface APIKeyCreated extends APIKey {
  key: string  // Only available at creation time
}

export interface APIKeyList {
  items: APIKey[]
  total: number
  max_keys: number
  api_calls_limit: number
  api_calls_used: number
}

export interface APIKeyCreateRequest {
  name: string
  description?: string
  expires_in_days?: number
}

// Client types (Mandantenverwaltung)
export interface Client {
  id: string
  name: string
  client_number?: string
  tax_number?: string
  vat_id?: string
  contact_name?: string
  contact_email?: string
  contact_phone?: string
  street?: string
  postal_code?: string
  city?: string
  country: string
  notes?: string
  is_active: boolean
  validation_count: number
  last_validation_at?: string
  created_at: string
  updated_at: string
}

export interface ClientListItem {
  id: string
  name: string
  client_number?: string
  is_active: boolean
  validation_count: number
  last_validation_at?: string
  created_at: string
}

export interface ClientList {
  items: ClientListItem[]
  total: number
  page: number
  page_size: number
  max_clients: number
}

export interface ClientStats {
  total_clients: number
  active_clients: number
  total_validations: number
  max_clients: number
}

export interface ClientCreateRequest {
  name: string
  client_number?: string
  tax_number?: string
  vat_id?: string
  contact_name?: string
  contact_email?: string
  contact_phone?: string
  street?: string
  postal_code?: string
  city?: string
  country?: string
  notes?: string
}

export interface ClientUpdateRequest extends Partial<ClientCreateRequest> {
  is_active?: boolean
}

// Conversion types
export type OutputFormat = 'xrechnung' | 'zugferd'
export type ZUGFeRDProfileType = 'MINIMUM' | 'BASIC' | 'EN16931' | 'EXTENDED'

export interface ExtractedData {
  invoice_number?: string
  invoice_date?: string
  due_date?: string
  delivery_date?: string
  seller_name?: string
  seller_street?: string
  seller_postal_code?: string
  seller_city?: string
  seller_vat_id?: string
  seller_tax_id?: string
  buyer_name?: string
  buyer_street?: string
  buyer_postal_code?: string
  buyer_city?: string
  buyer_reference?: string
  net_amount?: number
  vat_amount?: number
  gross_amount?: number
  currency: string
  iban?: string
  bic?: string
  bank_name?: string
  payment_reference?: string
  leitweg_id?: string
  order_reference?: string
  confidence: number
  warnings: string[]
}

export interface PreviewResponse {
  extracted_data: ExtractedData
  ocr_used: boolean
  ocr_available: boolean
}

export interface ConversionResponse {
  success: boolean
  conversion_id: string
  filename: string
  output_format: OutputFormat
  extracted_data: ExtractedData
  warnings: string[]
  error?: string
}

export interface ConversionStatusResponse {
  ocr_available: boolean
  supported_formats: OutputFormat[]
  supported_profiles: ZUGFeRDProfileType[]
}
