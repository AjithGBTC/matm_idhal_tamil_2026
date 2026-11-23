import axios, { InternalAxiosRequestConfig } from 'axios'

const client = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1', timeout: 12_000 })
let accessTokenInMemory: string | null = null
let refreshTokenInMemory: string | null = null
let refreshInFlight: Promise<void> | null = null

export function setAuthTokens(tokens: AuthResponse | null) {
  accessTokenInMemory = tokens?.access_token ?? null
  refreshTokenInMemory = tokens?.refresh_token ?? null
}

type RetryConfig = InternalAxiosRequestConfig & { _retried?: boolean }
client.interceptors.response.use(response => response, async (error: unknown) => {
  if (!axios.isAxiosError(error)) throw error
  const request = error.config as RetryConfig | undefined
  if (error.response?.status !== 401 || !request || request._retried || !refreshTokenInMemory || request.url?.includes('/auth/')) throw error
  request._retried = true
  if (!refreshInFlight) {
    const refreshToken = refreshTokenInMemory
    refreshInFlight = axios.post<AuthResponse>(`${client.defaults.baseURL}/auth/refresh`, { refresh_token: refreshToken }, { timeout: 12_000 })
      .then(response => { setAuthTokens(response.data) })
      .catch(reason => { setAuthTokens(null); throw reason })
      .finally(() => { refreshInFlight = null })
  }
  await refreshInFlight
  request.headers.Authorization = `Bearer ${accessTokenInMemory}`
  return client(request)
})

function authorization(token: string) { return { Authorization: `Bearer ${accessTokenInMemory ?? token}` } }

export type AuthResponse = { access_token: string; refresh_token: string; expires_in: number }
export type PlatformOverview = { tenants: { total: number; active: number; inactive: number; trial: number; pending: number }; active_subscriptions: number; plan_distribution: { plan: string; subscriptions: number }[]; monthly_recurring_revenue_paise: number | null; pending_payments: number | null; generated_at: string }
export type Tenant = { id: number; business_name: string; owner_name: string; email: string; mobile: string; district: string; status: string; created_at: string; plan_name: string | null; monthly_price_paise: number | null }
export type TenantPage = { items: Tenant[]; total: number; page: number; page_size: number }
export type Plan = { id: number; name: string; monthly_price_paise: number; annual_price_paise: number; trial_days: number; max_users: number; max_staff: number; max_agents: number; storage_limit_mb: number; features: Record<string, boolean>; is_active: boolean }

export async function signIn(email: string, password: string) {
  return (await client.post<AuthResponse>('/auth/super-admin/login', { email, password })).data
}

export async function signOut() {
  const refreshToken = refreshTokenInMemory
  try {
    if (refreshToken && accessTokenInMemory) {
      await client.post('/auth/logout', { refresh_token: refreshToken }, { headers: authorization(accessTokenInMemory) })
    }
  } finally {
    setAuthTokens(null)
  }
}

export async function getOverview(token: string) {
  return (await client.get<PlatformOverview>('/super-admin/overview', { headers: authorization(token) })).data
}

export async function getTenants(token: string, search: string, page: number) {
  return (await client.get<TenantPage>('/super-admin/tenants', { params: { q: search || undefined, page, page_size: 6 }, headers: authorization(token) })).data
}

export async function getPlans(token: string) {
  return (await client.get<Plan[]>('/super-admin/plans', { headers: authorization(token) })).data
}

export async function createTenant(token: string, body: { business_name: string; owner_name: string; email: string; mobile: string; district: string; plan_id: number; initial_password: string }) {
  return (await client.post('/super-admin/tenants', body, { headers: authorization(token) })).data
}

export function apiError(error: unknown) {
  if (axios.isAxiosError(error)) return error.response?.data?.detail || (error.code === 'ERR_NETWORK' ? 'Could not reach the API. Check that the backend is running.' : error.message)
  return 'Something went wrong. Please try again.'
}
