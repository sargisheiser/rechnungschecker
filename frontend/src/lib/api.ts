import axios, { AxiosError, AxiosRequestConfig } from 'axios'
import type {
  AuthTokens,
  LoginRequest,
  RegisterRequest,
  User,
  ValidationResult,
  ValidationApiResponse,
  ValidationHistory,
  Plan,
  UsageStats,
  Subscription,
  ApiError,
  FileType,
  ZugferdProfile,
  APIKey,
  APIKeyCreated,
  APIKeyList,
  APIKeyCreateRequest,
  Client,
  ClientList,
  ClientStats,
  ClientCreateRequest,
  ClientUpdateRequest,
  PreviewResponse,
  ConversionResponse,
  ConversionStatusResponse,
  OutputFormat,
  ZUGFeRDProfileType,
  Integration,
  IntegrationList,
  IntegrationCreateRequest,
  IntegrationUpdateRequest,
  IntegrationTestResponse,
  IntegrationType,
  Webhook,
  WebhookCreated,
  WebhookList,
  WebhookWithDeliveries,
  WebhookCreateRequest,
  WebhookUpdateRequest,
  WebhookTestResponse,
  ExportParams,
  Template,
  TemplateList,
  TemplateCreateRequest,
  TemplateUpdateRequest,
  TemplateType,
  PlatformStats,
  AdminUserList,
  AdminUserDetail,
  AdminUserUpdate,
  AdminAuditLogList,
  PlanTier,
} from '@/types'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token management
let accessToken: string | null = null

export const setAccessToken = (token: string | null) => {
  accessToken = token
  if (token) {
    localStorage.setItem('access_token', token)
  } else {
    localStorage.removeItem('access_token')
  }
}

export const getAccessToken = () => {
  if (!accessToken) {
    accessToken = localStorage.getItem('access_token')
  }
  return accessToken
}

export const setRefreshToken = (token: string | null) => {
  if (token) {
    localStorage.setItem('refresh_token', token)
  } else {
    localStorage.removeItem('refresh_token')
  }
}

export const getRefreshToken = () => localStorage.getItem('refresh_token')

// Request interceptor
api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = getRefreshToken()

      if (refreshToken) {
        try {
          const response = await axios.post<AuthTokens>('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          })

          setAccessToken(response.data.access_token)
          setRefreshToken(response.data.refresh_token)

          return api(originalRequest)
        } catch {
          // Refresh failed, clear tokens
          setAccessToken(null)
          setRefreshToken(null)
          window.location.href = '/login'
        }
      }
    }

    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: async (data: LoginRequest): Promise<AuthTokens> => {
    const response = await api.post<AuthTokens>('/auth/login', data)
    return response.data
  },

  register: async (data: RegisterRequest): Promise<User> => {
    const response = await api.post<User>('/auth/register', data)
    return response.data
  },

  // Google OAuth - redirects to Google's OAuth page
  googleLogin: () => {
    const redirectUri = encodeURIComponent(`${window.location.origin}/auth/google/callback`)
    window.location.href = `/api/v1/auth/google/login?redirect_uri=${redirectUri}`
  },

  // Exchange Google OAuth code for tokens
  googleCallback: async (code: string): Promise<AuthTokens> => {
    const response = await api.post<AuthTokens>('/auth/google/callback', { code })
    return response.data
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me')
    return response.data
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout')
  },

  updateProfile: async (data: {
    full_name?: string
    company_name?: string
    email_notifications?: boolean
    notify_validation_results?: boolean
    notify_weekly_summary?: boolean
    notify_marketing?: boolean
  }): Promise<User> => {
    const response = await api.patch<User>('/auth/me', data)
    return response.data
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  },

  deleteAccount: async (): Promise<void> => {
    await api.delete('/auth/me')
  },

  forgotPassword: async (email: string): Promise<void> => {
    await api.post('/auth/forgot-password', { email })
  },

  resetPassword: async (token: string, password: string): Promise<void> => {
    await api.post('/auth/reset-password', { token, new_password: password })
  },

  verifyEmail: async (data: { email: string; code: string }): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/verify-email', data)
    return response.data
  },

  resendVerification: async (email: string): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/resend-verification', { email })
    return response.data
  },
}

// Helper to transform backend validation response to frontend format
function transformValidationResponse(
  data: ValidationApiResponse,
  fileName: string
): ValidationResult {
  return {
    id: data.id,
    status: data.is_valid ? 'valid' : data.error_count > 0 ? 'invalid' : 'error',
    file_type: (data.file_type as FileType) || 'unknown',
    file_name: fileName,
    zugferd_profile: data.zugferd_profile as ZugferdProfile | undefined,
    errors: data.errors.map((e) => ({
      code: e.code,
      message: e.message_de,
      location: e.location,
      severity: e.severity as 'error' | 'warning' | 'info',
      suggestion: e.suggestion,
    })),
    warnings: data.warnings.map((w) => ({
      code: w.code,
      message: w.message_de,
      location: w.location,
      severity: w.severity as 'error' | 'warning' | 'info',
      suggestion: w.suggestion,
    })),
    validated_at: data.validated_at,
    can_download_report: !!data.report_url,
    guest_id: data.guest_id,
    validations_used: data.validations_used,
    validations_limit: data.validations_limit,
  }
}

// Validation API
export const validationApi = {
  validate: async (file: File): Promise<ValidationResult> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post<ValidationApiResponse>('/validate/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return transformValidationResponse(response.data, file.name)
  },

  validateGuest: async (file: File, guestId?: string): Promise<ValidationResult & { guest_id: string }> => {
    const formData = new FormData()
    formData.append('file', file)
    if (guestId) {
      formData.append('guest_id', guestId)
    }

    const response = await api.post<ValidationApiResponse>('/validate/guest', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    const result = transformValidationResponse(response.data, file.name)
    return { ...result, guest_id: response.data.guest_id || '' }
  },

  getHistory: async (page = 1, limit = 10): Promise<ValidationHistory> => {
    const response = await api.get<ValidationHistory>('/validate/history', {
      params: { page, page_size: limit },
    })
    return response.data
  },

  getResult: async (id: string): Promise<ValidationResult> => {
    const response = await api.get<ValidationResult>(`/validate/${id}`)
    return response.data
  },

  downloadReport: async (id: string): Promise<Blob> => {
    const response = await api.get(`/reports/${id}/pdf`, {
      responseType: 'blob',
    })
    return response.data
  },

  getValidationDetail: async (id: string) => {
    const response = await api.get(`/validate/${id}`)
    return response.data
  },

  updateNotes: async (id: string, notes: string | null) => {
    const response = await api.patch(`/validate/${id}/notes`, { notes })
    return response.data
  },
}

// Billing API
export const billingApi = {
  getPlans: async (): Promise<{ plans: Plan[] }> => {
    const response = await api.get<{ plans: Plan[] }>('/billing/plans')
    return response.data
  },

  getPlan: async (planId: string): Promise<Plan> => {
    const response = await api.get<Plan>(`/billing/plans/${planId}`)
    return response.data
  },

  getSubscription: async (): Promise<Subscription | null> => {
    try {
      const response = await api.get<Subscription>('/billing/subscription')
      return response.data
    } catch (error) {
      if ((error as AxiosError).response?.status === 404) {
        return null
      }
      throw error
    }
  },

  getUsage: async (): Promise<UsageStats> => {
    const response = await api.get<UsageStats>('/billing/usage')
    return response.data
  },

  createCheckout: async (
    plan: string,
    annual: boolean,
    successUrl: string,
    cancelUrl: string
  ): Promise<{ url: string }> => {
    const response = await api.post<{ checkout_url: string }>('/billing/checkout', {
      plan,
      annual,
      success_url: successUrl,
      cancel_url: cancelUrl,
    })
    return { url: response.data.checkout_url }
  },

  createPortalSession: async (returnUrl: string): Promise<{ url: string }> => {
    const response = await api.post<{ portal_url: string }>('/billing/portal', {
      return_url: returnUrl,
    })
    return { url: response.data.portal_url }
  },

  cancelSubscription: async (): Promise<void> => {
    await api.post('/billing/cancel')
  },
}

// Clients API (Mandantenverwaltung)
export const clientsApi = {
  list: async (page = 1, pageSize = 20, activeOnly = false, search?: string): Promise<ClientList> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      active_only: activeOnly.toString(),
    })
    if (search) params.set('search', search)
    const response = await api.get<ClientList>(`/clients/?${params}`)
    return response.data
  },

  getStats: async (): Promise<ClientStats> => {
    const response = await api.get<ClientStats>('/clients/stats')
    return response.data
  },

  get: async (id: string): Promise<Client> => {
    const response = await api.get<Client>(`/clients/${id}`)
    return response.data
  },

  create: async (data: ClientCreateRequest): Promise<Client> => {
    const response = await api.post<Client>('/clients/', data)
    return response.data
  },

  update: async (id: string, data: ClientUpdateRequest): Promise<Client> => {
    const response = await api.patch<Client>(`/clients/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/clients/${id}`)
  },
}

// API Keys API
export const apiKeysApi = {
  list: async (): Promise<APIKeyList> => {
    const response = await api.get<APIKeyList>('/api-keys/')
    return response.data
  },

  create: async (data: APIKeyCreateRequest): Promise<APIKeyCreated> => {
    const response = await api.post<APIKeyCreated>('/api-keys/', data)
    return response.data
  },

  get: async (id: string): Promise<APIKey> => {
    const response = await api.get<APIKey>(`/api-keys/${id}`)
    return response.data
  },

  update: async (id: string, data: { name?: string; description?: string; is_active?: boolean }): Promise<APIKey> => {
    const response = await api.patch<APIKey>(`/api-keys/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api-keys/${id}`)
  },
}

// Conversion API
export const conversionApi = {
  getStatus: async (): Promise<ConversionStatusResponse> => {
    const response = await api.get<ConversionStatusResponse>('/convert/status')
    return response.data
  },

  preview: async (file: File): Promise<PreviewResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<PreviewResponse>('/convert/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  convert: async (
    file: File,
    outputFormat: OutputFormat = 'xrechnung',
    zugferdProfile: ZUGFeRDProfileType = 'EN16931',
    embedInPdf: boolean = true,
    overrides?: {
      invoice_number?: string
      seller_vat_id?: string
      buyer_reference?: string
      leitweg_id?: string
    }
  ): Promise<ConversionResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('output_format', outputFormat)
    formData.append('zugferd_profile', zugferdProfile)
    formData.append('embed_in_pdf', embedInPdf.toString())

    if (overrides?.invoice_number) formData.append('invoice_number', overrides.invoice_number)
    if (overrides?.seller_vat_id) formData.append('seller_vat_id', overrides.seller_vat_id)
    if (overrides?.buyer_reference) formData.append('buyer_reference', overrides.buyer_reference)
    if (overrides?.leitweg_id) formData.append('leitweg_id', overrides.leitweg_id)

    const response = await api.post<ConversionResponse>('/convert/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  download: async (conversionId: string): Promise<Blob> => {
    const response = await api.get(`/convert/${conversionId}/download`, {
      responseType: 'blob',
    })
    return response.data
  },

  previewXml: async (conversionId: string): Promise<string> => {
    const response = await api.get(`/convert/${conversionId}/preview-xml`, {
      responseType: 'text',
    })
    return response.data
  },

  convertBatch: async (
    files: File[],
    outputFormat: OutputFormat = 'xrechnung',
    zugferdProfile: ZUGFeRDProfileType = 'EN16931'
  ): Promise<ConversionResponse[]> => {
    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))
    formData.append('output_format', outputFormat)
    formData.append('zugferd_profile', zugferdProfile)

    const response = await api.post<ConversionResponse[]>('/convert/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  sendEmail: async (
    conversionId: string,
    recipientEmail?: string,
    sendCopyToSelf: boolean = false
  ): Promise<{ success: boolean; message: string; emails_sent: number }> => {
    const response = await api.post<{ success: boolean; message: string; emails_sent: number }>(
      `/convert/${conversionId}/send-email`,
      {
        recipient_email: recipientEmail || null,
        send_copy_to_self: sendCopyToSelf,
      }
    )
    return response.data
  },
}

// Integrations API
export const integrationsApi = {
  list: async (): Promise<IntegrationList> => {
    const response = await api.get<IntegrationList>('/integrations/')
    return response.data
  },

  create: async (type: IntegrationType, data: IntegrationCreateRequest): Promise<Integration> => {
    const response = await api.post<Integration>(`/integrations/${type}`, data)
    return response.data
  },

  update: async (type: IntegrationType, data: IntegrationUpdateRequest): Promise<Integration> => {
    const response = await api.patch<Integration>(`/integrations/${type}`, data)
    return response.data
  },

  delete: async (type: IntegrationType): Promise<void> => {
    await api.delete(`/integrations/${type}`)
  },

  test: async (type: IntegrationType): Promise<IntegrationTestResponse> => {
    const response = await api.post<IntegrationTestResponse>(`/integrations/${type}/test`)
    return response.data
  },
}

// Webhooks API
export const webhooksApi = {
  list: async (): Promise<WebhookList> => {
    const response = await api.get<WebhookList>('/webhooks/')
    return response.data
  },

  create: async (data: WebhookCreateRequest): Promise<WebhookCreated> => {
    const response = await api.post<WebhookCreated>('/webhooks/', data)
    return response.data
  },

  get: async (id: string): Promise<WebhookWithDeliveries> => {
    const response = await api.get<WebhookWithDeliveries>(`/webhooks/${id}`)
    return response.data
  },

  update: async (id: string, data: WebhookUpdateRequest): Promise<Webhook> => {
    const response = await api.patch<Webhook>(`/webhooks/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/webhooks/${id}`)
  },

  test: async (id: string): Promise<WebhookTestResponse> => {
    const response = await api.post<WebhookTestResponse>(`/webhooks/${id}/test`)
    return response.data
  },

  rotateSecret: async (id: string): Promise<WebhookCreated> => {
    const response = await api.post<WebhookCreated>(`/webhooks/${id}/rotate-secret`)
    return response.data
  },
}

// Analytics API
export interface AnalyticsDashboard {
  period: {
    start: string
    end: string
    days: number
  }
  summary: {
    total_validations: number
    valid_count: number
    invalid_count: number
    success_rate: number
    avg_processing_time_ms: number
    total_errors: number
    total_warnings: number
  }
  by_type: {
    xrechnung: number
    zugferd: number
  }
  by_day: Array<{
    date: string
    valid: number
    invalid: number
  }>
  top_errors: Array<{
    file_name: string
    error_count: number
    warning_count: number
    file_type: string
  }>
  usage: {
    validations_used: number
    validations_limit: number | null
    conversions_used: number
    conversions_limit: number | null
    plan: string
  }
}

export interface ClientComparison {
  client_id: string
  client_name: string
  total_validations: number
  valid_count: number
  invalid_count: number
  success_rate: number
}

export const analyticsApi = {
  getDashboard: async (days = 30, clientId?: string): Promise<AnalyticsDashboard> => {
    const params = new URLSearchParams({ days: days.toString() })
    if (clientId) params.set('client_id', clientId)
    const response = await api.get<AnalyticsDashboard>(`/analytics/dashboard?${params}`)
    return response.data
  },

  getClientComparison: async (days = 30): Promise<ClientComparison[]> => {
    const response = await api.get<ClientComparison[]>(`/analytics/clients?days=${days}`)
    return response.data
  },
}

// Export API
export const exportApi = {
  downloadValidations: async (params: ExportParams = {}): Promise<Blob> => {
    const queryParams = new URLSearchParams()
    if (params.client_id) queryParams.set('client_id', params.client_id)
    if (params.date_from) queryParams.set('date_from', params.date_from)
    if (params.date_to) queryParams.set('date_to', params.date_to)
    if (params.status) queryParams.set('status', params.status)
    if (params.format) queryParams.set('format', params.format)

    const response = await api.get(`/export/validations?${queryParams}`, {
      responseType: 'blob',
    })
    return response.data
  },

  downloadClients: async (params: {
    include_inactive?: boolean
    date_from?: string
    date_to?: string
    format?: 'datev' | 'excel'
  } = {}): Promise<Blob> => {
    const queryParams = new URLSearchParams()
    if (params.include_inactive) queryParams.set('include_inactive', 'true')
    if (params.date_from) queryParams.set('date_from', params.date_from)
    if (params.date_to) queryParams.set('date_to', params.date_to)
    if (params.format) queryParams.set('format', params.format)

    const response = await api.get(`/export/clients?${queryParams}`, {
      responseType: 'blob',
    })
    return response.data
  },
}

// Batch API
export type BatchJobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
export type BatchFileStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'skipped'

export interface BatchFile {
  id: string
  filename: string
  file_size_bytes: number
  status: BatchFileStatus
  validation_id: string | null
  error_message: string | null
  processed_at: string | null
}

export interface BatchJob {
  id: string
  name: string
  status: BatchJobStatus
  total_files: number
  processed_files: number
  successful_count: number
  failed_count: number
  progress_percent: number
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  client_id: string | null
}

export interface BatchJobCreated {
  id: string
  name: string
  total_files: number
  status: BatchJobStatus
  message: string
}

export interface BatchJobWithFiles extends BatchJob {
  files: BatchFile[]
}

export interface BatchJobList {
  items: BatchJob[]
  total: number
  page: number
  page_size: number
}

export interface BatchFileResult {
  filename: string
  is_valid: boolean | null
  error_count: number
  warning_count: number
  validation_id: string | null
  error_message: string | null
}

export interface BatchResultsSummary {
  job_id: string
  job_name: string
  status: BatchJobStatus
  total_files: number
  successful_count: number
  failed_count: number
  valid_count: number
  invalid_count: number
  results: BatchFileResult[]
}

export const batchApi = {
  create: async (files: File[], name?: string, clientId?: string): Promise<BatchJobCreated> => {
    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))
    if (name) formData.append('name', name)
    if (clientId) formData.append('client_id', clientId)

    const response = await api.post<BatchJobCreated>('/batch/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  list: async (page = 1, pageSize = 20): Promise<BatchJobList> => {
    const response = await api.get<BatchJobList>(`/batch/jobs?page=${page}&page_size=${pageSize}`)
    return response.data
  },

  get: async (jobId: string): Promise<BatchJobWithFiles> => {
    const response = await api.get<BatchJobWithFiles>(`/batch/jobs/${jobId}`)
    return response.data
  },

  getResults: async (jobId: string): Promise<BatchResultsSummary> => {
    const response = await api.get<BatchResultsSummary>(`/batch/jobs/${jobId}/results`)
    return response.data
  },

  cancel: async (jobId: string): Promise<void> => {
    await api.post(`/batch/jobs/${jobId}/cancel`)
  },

  delete: async (jobId: string): Promise<void> => {
    await api.delete(`/batch/jobs/${jobId}`)
  },
}

// Templates API
export const templatesApi = {
  list: async (page = 1, pageSize = 50, templateType?: TemplateType): Promise<TemplateList> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    })
    if (templateType) params.set('template_type', templateType)
    const response = await api.get<TemplateList>(`/templates/?${params}`)
    return response.data
  },

  get: async (id: string): Promise<Template> => {
    const response = await api.get<Template>(`/templates/${id}`)
    return response.data
  },

  create: async (data: TemplateCreateRequest): Promise<Template> => {
    const response = await api.post<Template>('/templates/', data)
    return response.data
  },

  update: async (id: string, data: TemplateUpdateRequest): Promise<Template> => {
    const response = await api.patch<Template>(`/templates/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/templates/${id}`)
  },

  setDefault: async (id: string): Promise<Template> => {
    const response = await api.post<Template>(`/templates/${id}/set-default`)
    return response.data
  },
}

// Admin API
export const adminApi = {
  getStats: async (): Promise<PlatformStats> => {
    const response = await api.get<PlatformStats>('/admin/stats')
    return response.data
  },

  listUsers: async (
    page = 1,
    pageSize = 20,
    search?: string,
    plan?: PlanTier,
    isActive?: boolean
  ): Promise<AdminUserList> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    })
    if (search) params.set('search', search)
    if (plan) params.set('plan', plan)
    if (isActive !== undefined) params.set('is_active', isActive.toString())
    const response = await api.get<AdminUserList>(`/admin/users?${params}`)
    return response.data
  },

  getUser: async (userId: string): Promise<AdminUserDetail> => {
    const response = await api.get<AdminUserDetail>(`/admin/users/${userId}`)
    return response.data
  },

  updateUser: async (userId: string, data: AdminUserUpdate): Promise<AdminUserDetail> => {
    const response = await api.patch<AdminUserDetail>(`/admin/users/${userId}`, data)
    return response.data
  },

  deleteUser: async (userId: string): Promise<void> => {
    await api.delete(`/admin/users/${userId}`)
  },

  getAuditLogs: async (
    page = 1,
    pageSize = 50,
    userId?: string,
    action?: string
  ): Promise<AdminAuditLogList> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    })
    if (userId) params.set('user_id', userId)
    if (action) params.set('action', action)
    const response = await api.get<AdminAuditLogList>(`/admin/audit?${params}`)
    return response.data
  },
}

export default api
