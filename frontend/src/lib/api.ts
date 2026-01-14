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

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me')
    return response.data
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout')
  },

  updateProfile: async (data: { company_name?: string }): Promise<User> => {
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
    })),
    warnings: data.warnings.map((w) => ({
      code: w.code,
      message: w.message_de,
      location: w.location,
      severity: w.severity as 'error' | 'warning' | 'info',
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
      params: { page, limit },
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

export default api
