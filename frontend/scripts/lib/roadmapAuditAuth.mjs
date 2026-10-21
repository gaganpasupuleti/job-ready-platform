/**
 * @returns {Promise<Record<string, string>>}
 */
export async function resolveAuthHeaders(apiBase) {
  const token = process.env.ROADMAP_AUDIT_TOKEN?.trim()
  if (token) {
    const headers = { Authorization: `Bearer ${token}` }
    const verified = await verifyAuthHeaders(apiBase, headers)
    if (!verified.ok) {
      const err = new Error(`ROADMAP_AUDIT_TOKEN rejected: HTTP ${verified.status ?? 'unknown'}`)
      err.code = 'AUTH_TOKEN_INVALID'
      throw err
    }
    return headers
  }

  const email = process.env.ROADMAP_AUDIT_EMAIL?.trim()
  const password = process.env.ROADMAP_AUDIT_PASSWORD
  if (!email || !password) {
    const err = new Error(
      'Set ROADMAP_AUDIT_TOKEN or ROADMAP_AUDIT_EMAIL and ROADMAP_AUDIT_PASSWORD for catalog audit.',
    )
    err.code = 'AUTH_MISSING'
    throw err
  }

  const res = await fetch(`${apiBase}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const err = new Error(`audit login failed: HTTP ${res.status}`)
    err.code = 'AUTH_LOGIN_FAILED'
    throw err
  }
  const body = await res.json()
  if (!body?.access_token) {
    const err = new Error('audit login missing access_token')
    err.code = 'AUTH_LOGIN_FAILED'
    throw err
  }
  return { Authorization: `Bearer ${body.access_token}` }
}

/**
 * @param {Record<string, string>} authHeaders
 */
export async function verifyAuthHeaders(apiBase, authHeaders) {
  if (!authHeaders?.Authorization) {
    return { ok: false, status: 0, reason: 'missing' }
  }
  const res = await fetch(`${apiBase}/api/v1/auth/me`, {
    headers: { Accept: 'application/json', ...authHeaders },
  })
  return { ok: res.ok, status: res.status, reason: res.ok ? undefined : 'rejected' }
}
