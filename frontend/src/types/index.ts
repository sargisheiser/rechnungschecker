// User types
export interface User {
  id: string
  email: string
  company_name?: string
  full_name?: string
  plan: PlanTier
  is_active: boolean
  is_verified: boolean
  is_admin: boolean
  created_at: string

  // Notification preferences
  email_notifications: boolean
  notify_validation_results: boolean
  notify_weekly_summary: boolean
  notify_marketing: boolean
}

// Admin types
export interface AdminUserListItem {
  id: string
  email: string
  full_name?: string
  company_name?: string
  plan: PlanTier
  is_active: boolean
  is_verified: boolean
  is_admin: boolean
  validations_this_month: number
  conversions_this_month: number
  created_at: string
  last_login_at?: string
}

export interface AdminUserDetail extends AdminUserListItem {
  stripe_customer_id?: string
  stripe_subscription_id?: string
  plan_valid_until?: string
  updated_at: string
  email_notifications: boolean
  notify_validation_results: boolean
  notify_weekly_summary: boolean
  notify_marketing: boolean
}

export interface AdminUserList {
  items: AdminUserListItem[]
  total: number
  page: number
  page_size: number
}

export interface AdminUserUpdate {
  is_active?: boolean
  is_verified?: boolean
  is_admin?: boolean
  plan?: PlanTier
  full_name?: string
  company_name?: string
}

export interface PlatformStats {
  total_users: number
  active_users: number
  verified_users: number
  total_validations: number
  total_conversions: number
  validations_today: number
  validations_this_week: number
  validations_this_month: number
  users_by_plan: Record<string, number>
  recent_registrations: AdminUserListItem[]
}

export interface AdminAuditLogItem {
  id: string
  user_id: string
  user_email?: string
  action: string
  resource_type?: string
  resource_id?: string
  ip_address?: string
  user_agent?: string
  details?: Record<string, unknown>
  created_at: string
}

export interface AdminAuditLogList {
  items: AdminAuditLogItem[]
  total: number
  page: number
  page_size: number
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
  suggestion?: string
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

export interface LineItem {
  description: string
  quantity: number
  unit: string
  unit_price: number
  vat_rate: number
  total: number
}

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
  net_amount?: string | number
  vat_amount?: string | number
  gross_amount?: string | number
  currency: string
  iban?: string
  bic?: string
  bank_name?: string
  payment_reference?: string
  leitweg_id?: string
  order_reference?: string
  confidence: number
  warnings: string[]
  line_items?: LineItem[]
}

export interface PreviewResponse {
  extracted_data: ExtractedData
  ocr_used: boolean
  ocr_available: boolean
  ai_used: boolean
}

export interface ConversionValidationError {
  severity: string
  code: string
  message_de: string
  message_en?: string
  location?: string
  suggestion?: string
}

export interface ConversionValidationResult {
  is_valid: boolean
  error_count: number
  warning_count: number
  info_count: number
  errors: ConversionValidationError[]
  warnings: ConversionValidationError[]
  infos: ConversionValidationError[]
  validator_version?: string
  processing_time_ms?: number
}

export interface ConversionResponse {
  success: boolean
  conversion_id: string
  filename: string
  output_format: OutputFormat
  extracted_data: ExtractedData
  warnings: string[]
  error?: string
  validation_result?: ConversionValidationResult
}

export interface ConversionStatusResponse {
  ocr_available: boolean
  ai_available: boolean
  supported_formats: OutputFormat[]
  supported_profiles: ZUGFeRDProfileType[]
}

// Integration types
export type IntegrationType = 'lexoffice' | 'slack' | 'teams'

export interface Integration {
  id: string
  integration_type: IntegrationType
  is_enabled: boolean
  notify_on_valid: boolean
  notify_on_invalid: boolean
  notify_on_warning: boolean
  last_used_at?: string
  total_requests: number
  successful_requests: number
  failed_requests: number
  created_at: string
  updated_at: string
  config_hint?: string
}

export interface IntegrationList {
  items: Integration[]
}

export interface IntegrationCreateRequest {
  config: Record<string, string>
  notify_on_valid?: boolean
  notify_on_invalid?: boolean
  notify_on_warning?: boolean
}

export interface IntegrationUpdateRequest {
  is_enabled?: boolean
  notify_on_valid?: boolean
  notify_on_invalid?: boolean
  notify_on_warning?: boolean
}

export interface IntegrationTestResponse {
  success: boolean
  message: string
}

// Webhook types
export type WebhookEventType = 'validation.completed' | 'validation.failed' | 'test'

export interface Webhook {
  id: string
  url: string
  events: string[]
  description?: string
  is_active: boolean
  total_deliveries: number
  successful_deliveries: number
  failed_deliveries: number
  last_triggered_at?: string
  last_success_at?: string
  created_at: string
  updated_at: string
}

export interface WebhookCreated extends Webhook {
  secret: string
}

export interface WebhookList {
  items: Webhook[]
  total: number
  max_webhooks: number
}

export interface WebhookDelivery {
  id: string
  event_type: string
  event_id: string
  status: 'pending' | 'success' | 'failed' | 'retrying'
  attempt_count: number
  response_status_code?: number
  response_time_ms?: number
  error_message?: string
  created_at: string
  last_attempt_at?: string
  completed_at?: string
}

export interface WebhookWithDeliveries extends Webhook {
  recent_deliveries: WebhookDelivery[]
}

export interface WebhookCreateRequest {
  url: string
  events: WebhookEventType[]
  description?: string
}

export interface WebhookUpdateRequest {
  url?: string
  events?: WebhookEventType[]
  description?: string
  is_active?: boolean
}

export interface WebhookTestResponse {
  success: boolean
  delivery_id: string
  message: string
  response_status_code?: number
  response_time_ms?: number
}

// Export types
export type ExportFormat = 'datev' | 'excel'
export type ExportValidationStatus = 'all' | 'valid' | 'invalid'

export interface ExportParams {
  client_id?: string
  date_from?: string
  date_to?: string
  status?: ExportValidationStatus
  format?: ExportFormat
}

// Template types
export type TemplateType = 'sender' | 'receiver'

export interface Template {
  id: string
  name: string
  template_type: TemplateType
  company_name: string
  street?: string
  postal_code?: string
  city?: string
  country_code: string
  vat_id?: string
  tax_id?: string
  email?: string
  phone?: string
  iban?: string
  bic?: string
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface TemplateListItem {
  id: string
  name: string
  template_type: TemplateType
  company_name: string
  city?: string
  is_default: boolean
  created_at: string
}

export interface TemplateList {
  items: TemplateListItem[]
  total: number
  page: number
  page_size: number
}

export interface TemplateCreateRequest {
  name: string
  template_type: TemplateType
  company_name: string
  street?: string
  postal_code?: string
  city?: string
  country_code?: string
  vat_id?: string
  tax_id?: string
  email?: string
  phone?: string
  iban?: string
  bic?: string
  is_default?: boolean
}

export interface TemplateUpdateRequest extends Partial<TemplateCreateRequest> {}

// Organization/Team types
export type OrganizationRole = 'owner' | 'admin' | 'member'

export interface Organization {
  id: string
  name: string
  slug: string
  description?: string
  owner_id: string
  plan: PlanTier
  max_members: number
  is_active: boolean
  validations_this_month: number
  conversions_this_month: number
  member_count?: number
  created_at: string
}

export interface OrganizationList {
  organizations: Organization[]
  total: number
}

export interface OrganizationCreateRequest {
  name: string
  description?: string
}

export interface OrganizationUpdateRequest {
  name?: string
  description?: string
}

export interface OrganizationMember {
  id: string
  user_id: string
  email: string
  full_name?: string
  role: OrganizationRole
  invited_at: string
  joined_at?: string
}

export interface OrganizationMemberList {
  members: OrganizationMember[]
  total: number
}

export interface MemberInviteRequest {
  email: string
  role: 'admin' | 'member'
}

export interface MemberUpdateRequest {
  role: 'admin' | 'member'
}

export interface OrganizationInvitation {
  id: string
  email: string
  role: OrganizationRole
  organization_name: string
  expires_at: string
  is_valid: boolean
}

// Invoice Creator types
export interface PartyAddress {
  street?: string
  city?: string
  postal_code?: string
  country: string
}

export interface PartyInfo {
  name: string
  address?: PartyAddress
  tax_id?: string
  vat_id?: string
  email?: string
  phone?: string
  iban?: string
  bic?: string
  bank_name?: string
}

export interface InvoiceLineItem {
  id?: string
  description: string
  quantity: number
  unit: string
  unit_price: number
  tax_rate: number
  tax_category: string
}

export interface PaymentInfo {
  payment_terms?: string
  payment_means_code: string
  due_date?: string
  iban?: string
  bic?: string
  bank_name?: string
}

export interface InvoiceReferences {
  order_reference?: string
  buyer_reference?: string
  contract_reference?: string
  project_reference?: string
}

export interface InvoiceData {
  invoice_number?: string
  invoice_date?: string
  due_date?: string
  currency: string
  seller?: PartyInfo
  buyer?: PartyInfo
  line_items: InvoiceLineItem[]
  payment?: PaymentInfo
  references?: InvoiceReferences
  note?: string
}

export interface InvoiceDraft {
  id: string
  user_id: string
  client_id?: string
  name: string
  output_format: 'xrechnung' | 'zugferd'
  invoice_data: InvoiceData
  current_step: number
  is_complete: boolean
  generated_xml?: string
  validation_result_id?: string
  created_at: string
  updated_at: string
}

export interface InvoiceDraftListItem {
  id: string
  name: string
  output_format: string
  current_step: number
  is_complete: boolean
  created_at: string
  updated_at: string
}

export interface InvoiceDraftList {
  drafts: InvoiceDraftListItem[]
  total: number
}

export interface InvoiceDraftCreateRequest {
  name?: string
  output_format?: 'xrechnung' | 'zugferd'
  client_id?: string
}

export interface InvoiceDraftUpdateRequest {
  name?: string
  output_format?: 'xrechnung' | 'zugferd'
  current_step?: number
  invoice_data?: InvoiceData
}

export interface GenerateInvoiceResponse {
  id: string
  xml: string
  is_valid: boolean
  validation_errors: string[]
  validation_warnings: string[]
}

// Scheduled Validation Types
export type CloudStorageProvider = 's3' | 'gcs' | 'azure_blob'
export type ScheduledJobStatus = 'active' | 'paused' | 'error'
export type ScheduledRunStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface S3Credentials {
  access_key_id: string
  secret_access_key: string
  region: string
}

export interface CloudCredentials {
  s3?: S3Credentials
}

export interface ScheduledValidationJob {
  id: string
  name: string
  provider: CloudStorageProvider
  bucket_name: string
  prefix: string | null
  file_pattern: string
  schedule_cron: string
  timezone: string
  is_enabled: boolean
  status: ScheduledJobStatus
  delete_after_validation: boolean
  move_to_folder: string | null
  webhook_url: string | null
  last_run_at: string | null
  last_run_status: string | null
  total_runs: number
  total_files_validated: number
  total_files_valid: number
  total_files_invalid: number
  created_at: string
}

export interface ScheduledValidationRun {
  id: string
  job_id: string
  status: ScheduledRunStatus
  started_at: string
  completed_at: string | null
  files_found: number
  files_validated: number
  files_valid: number
  files_invalid: number
  files_failed: number
  error_message: string | null
}

export interface ScheduledValidationFile {
  id: string
  file_key: string
  file_name: string
  file_size_bytes: number
  is_valid: boolean | null
  error_count: number
  warning_count: number
  validation_log_id: string | null
  error_message: string | null
}

export interface CreateScheduledJobRequest {
  name: string
  provider: CloudStorageProvider
  credentials: CloudCredentials
  bucket_name: string
  prefix?: string
  file_pattern?: string
  schedule_cron: string
  timezone?: string
  delete_after_validation?: boolean
  move_to_folder?: string
  webhook_url?: string
}

export interface UpdateScheduledJobRequest {
  name?: string
  prefix?: string
  file_pattern?: string
  schedule_cron?: string
  timezone?: string
  is_enabled?: boolean
  delete_after_validation?: boolean
  move_to_folder?: string
  webhook_url?: string
}

export interface TestConnectionRequest {
  provider: CloudStorageProvider
  credentials: CloudCredentials
  bucket_name: string
}

export interface TestConnectionResponse {
  success: boolean
  message: string
}
