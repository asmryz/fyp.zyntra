/**
 * Small wrapper around fetch() for talking to the FastAPI backend.
 *
 * - The short-lived access token is kept in memory only (not localStorage),
 *   so other scripts on the page cannot read it from storage.
 * - The refresh token is an HttpOnly cookie that the browser sends to
 *   /api/auth/refresh automatically. When a request fails with 401, we try one
 *   refresh and repeat the request.
 * - Backend error responses are turned into readable messages.
 */

let accessToken = null
let refreshPromise = null
let sessionListener = null

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
  }
}

export function setAccessToken(token) {
  accessToken = token
}

/** AuthContext registers a callback so it hears about refreshed or expired sessions. */
export function onSessionChange(listener) {
  sessionListener = listener
}

function humanizeField(name) {
  const text = String(name).replace(/_/g, ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

function formatValidationError(error) {
  const message = (error.msg || 'Invalid value').replace(/^Value error, /, '')
  const field = (error.loc || []).filter((part) => part !== 'body' && typeof part === 'string').pop()
  return field ? `${humanizeField(field)}: ${message}` : message
}

export function errorMessage(data, status) {
  const detail = data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(formatValidationError).join(' ')
  if (detail?.message) return detail.message
  if (status === 429) return 'Too many attempts. Please wait a moment and try again.'
  if (status >= 500) return 'The server ran into a problem. Please try again.'
  return 'Something went wrong. Please try again.'
}

async function sendRequest(method, path, body) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`

  try {
    return await fetch(path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      credentials: 'include',
    })
  } catch {
    throw new ApiError('Cannot reach the ZYNTRA server. Please check your connection and that the backend is running.', 0)
  }
}

/**
 * Ask the backend for a new access token using the refresh cookie.
 * Several callers at the same time share one request.
 */
export function refreshSession() {
  if (!refreshPromise) {
    refreshPromise = sendRequest('POST', '/api/auth/refresh')
      .then(async (response) => {
        // 204 means the browser has no login cookie at all: the visitor is simply logged out
        if (response.status === 204) throw new ApiError('Not logged in.', 401)
        const data = await response.json().catch(() => null)
        if (!response.ok) throw new ApiError(errorMessage(data, response.status), response.status, data)
        accessToken = data.access_token
        sessionListener?.(data.user)
        return data
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

export async function apiRequest(method, path, body) {
  let response = await sendRequest(method, path, body)

  const canRetry = response.status === 401 && accessToken && !path.startsWith('/api/auth/')
  if (canRetry) {
    try {
      await refreshSession()
      response = await sendRequest(method, path, body)
    } catch {
      accessToken = null
      sessionListener?.(null)
    }
  }

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(errorMessage(data, response.status), response.status, data)
  }
  return data
}

export const api = {
  get: (path) => apiRequest('GET', path),
  post: (path, body = {}) => apiRequest('POST', path, body),
  put: (path, body) => apiRequest('PUT', path, body),
  patch: (path, body) => apiRequest('PATCH', path, body),
  delete: (path) => apiRequest('DELETE', path),
}
