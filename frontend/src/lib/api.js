import axios from 'axios'
import { AUTH_API_URL, MARKET_API_URL } from '../config'

export const TOKEN_KEY = 'ab_access_token'
export const REFRESH_KEY = 'ab_refresh_token'
export const USER_KEY = 'ab_user'

export const authApi = axios.create({ baseURL: AUTH_API_URL })
export const marketApi = axios.create({ baseURL: MARKET_API_URL })

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY)
}
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY)
}
export function setTokens(access, refresh) {
  if (access) localStorage.setItem(TOKEN_KEY, access)
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
}
export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(USER_KEY)
}

function attachToken(config) {
  const token = getAccessToken()
  if (token) {
    config.headers = { ...config.headers, Authorization: `Bearer ${token}` }
  }
  return config
}

authApi.interceptors.request.use(attachToken)
marketApi.interceptors.request.use(attachToken)

async function tryRefresh() {
  const refresh = getRefreshToken()
  if (!refresh) return null
  const { data } = await authApi.post('/api/auth/refresh', { refresh_token: refresh })
  setTokens(data.access_token, data.refresh_token)
  return data.access_token
}

// Auto-refresh on 401 once, then bounce to /login and notify other tabs.
function installRefresh(api) {
  let refreshing = null
  api.interceptors.response.use(
    (res) => res,
    async (error) => {
      const original = error.config
      if (error.response?.status === 401 && !original?._retry) {
        original._retry = true
        if (!refreshing) refreshing = tryRefresh().finally(() => (refreshing = null))
        const token = await refreshing
        if (token) {
          original.headers.Authorization = `Bearer ${token}`
          return api(original)
        }
        clearTokens()
        window.dispatchEvent(new CustomEvent('ab:logout'))
        const next = encodeURIComponent(window.location.pathname + window.location.search)
        window.location.assign(`/login?next=${next}`)
      }
      return Promise.reject(error)
    },
  )
}
installRefresh(authApi)
installRefresh(marketApi)

export function apiErrorMessage(error, fallback = 'Something went wrong') {
  return error?.response?.data?.error?.message || error?.message || fallback
}