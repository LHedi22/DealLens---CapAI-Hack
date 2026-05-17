const BASE = '/api'

export async function getPipeline() {
  const res = await fetch(`${BASE}/pipeline`)
  if (!res.ok) throw new Error('Failed to fetch pipeline')
  return res.json()
}

export async function getDeal(id) {
  const res = await fetch(`${BASE}/pipeline/${id}`)
  if (!res.ok) throw new Error('Deal not found')
  return res.json()
}

export async function uploadFiles(startupId, files) {
  const form = new FormData()
  form.append('startup_id', startupId)
  files.forEach(f => form.append('files', f))
  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form })
  if (!res.ok) throw new Error('Upload failed')
  return res.json()
}

export async function submitProfile(profile) {
  const res = await fetch(`${BASE}/startup/profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  })
  if (!res.ok) throw new Error('Profile submission failed')
  return res.json()
}

export async function getMandate() {
  const res = await fetch(`${BASE}/mandate`)
  if (!res.ok) throw new Error('Failed to fetch mandate')
  return res.json()
}

export async function saveMandate(mandate) {
  const res = await fetch(`${BASE}/mandate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(mandate),
  })
  if (!res.ok) throw new Error('Failed to save mandate')
  return res.json()
}

export async function applyMandate() {
  const res = await fetch(`${BASE}/mandate/apply`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to apply mandate')
  return res.json()
}

export async function evaluateStartup(payload) {
  const res = await fetch(`${BASE}/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Evaluation failed')
  }
  return res.json()
}

export async function getCachedEvaluation(startupName) {
  const res = await fetch(`${BASE}/evaluate/cached/${encodeURIComponent(startupName)}`)
  if (res.status === 404) return null
  if (!res.ok) throw new Error('Failed to fetch cached evaluation')
  return res.json()
}

export async function getOcrMock() {
  const res = await fetch(`${BASE}/ocr-mock`)
  if (!res.ok) throw new Error('Failed to fetch OCR mock data')
  return res.json()
}

export async function confirmOcr(payload) {
  const res = await fetch(`${BASE}/ocr-confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'OCR confirmation failed')
  }
  return res.json()
}

// ── Monitor API ───────────────────────────────────────────────────────────────

export async function uploadMonitorStatement(startupName, file) {
  const form = new FormData()
  form.append('startup_name', startupName)
  form.append('file', file)
  const res = await fetch(`${BASE}/monitor/statement/upload`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Statement upload failed')
  }
  return res.json()
}

export async function getMonitorTransactions(startupName, { page = 1, pageSize = 50, category = '', status = '', month = '' } = {}) {
  const params = new URLSearchParams({ page, page_size: pageSize })
  if (category) params.set('category', category)
  if (status)   params.set('status', status)
  if (month)    params.set('month', month)
  const res = await fetch(`${BASE}/monitor/transactions/${encodeURIComponent(startupName)}?${params}`)
  if (!res.ok) throw new Error('Failed to fetch transactions')
  return res.json()
}

export async function reclassifyTransaction(txId, category) {
  const res = await fetch(`${BASE}/monitor/transaction/${txId}/classify`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ category }),
  })
  if (!res.ok) throw new Error('Reclassification failed')
  return res.json()
}

export async function getMonitorAlerts(startupName) {
  const res = await fetch(`${BASE}/monitor/alerts/${encodeURIComponent(startupName)}`)
  if (!res.ok) throw new Error('Failed to fetch alerts')
  return res.json()
}

export async function resolveMonitorAlert(alertId, note = '') {
  const res = await fetch(`${BASE}/monitor/alert/${alertId}/resolve`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ note }),
  })
  if (!res.ok) throw new Error('Failed to resolve alert')
  return res.json()
}

export async function getMonitorTimeline(startupName) {
  const res = await fetch(`${BASE}/monitor/timeline/${encodeURIComponent(startupName)}`)
  if (!res.ok) throw new Error('Failed to fetch timeline')
  return res.json()
}

export async function getMonitorOcrMock() {
  const res = await fetch(`${BASE}/monitor/ocr-mock`)
  if (!res.ok) throw new Error('Failed to fetch monitor OCR mock data')
  return res.json()
}

export async function confirmMonitorOcr(payload) {
  const res = await fetch(`${BASE}/monitor/ocr-confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'OCR confirmation failed')
  }
  return res.json()
}

export async function markNoStatement(startupName, month) {
  const res = await fetch(`${BASE}/monitor/statement/no-statement`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ startup_name: startupName, month }),
  })
  if (!res.ok) throw new Error('Failed to mark no-statement')
  return res.json()
}

// ── Synergy API ───────────────────────────────────────────────────────────────

export async function getSynergyStatus() {
  const res = await fetch(`${BASE}/synergy/status`)
  if (!res.ok) throw new Error('Failed to fetch synergy status')
  return res.json()
}

export async function runSynergy() {
  const res = await fetch(`${BASE}/synergy/run`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to run synergy engine')
  return res.json()
}

export async function getSynergyPairs({ type, decision } = {}) {
  const params = new URLSearchParams()
  if (type)     params.set('type', type)
  if (decision) params.set('decision', decision)
  const q = params.toString() ? `?${params}` : ''
  const res = await fetch(`${BASE}/synergy/pairs${q}`)
  if (!res.ok) throw new Error('Failed to fetch synergy pairs')
  return res.json()
}

export async function getSynergyGraph() {
  const res = await fetch(`${BASE}/synergy/graph`)
  if (!res.ok) throw new Error('Failed to fetch synergy graph')
  return res.json()
}

export async function decideSynergyPair(pairId, { decision, reason = '', snoozeDays = 0 }) {
  const res = await fetch(`${BASE}/synergy/pairs/${pairId}/decide`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, reason, snooze_days: snoozeDays }),
  })
  if (!res.ok) throw new Error('Failed to record synergy decision')
  return res.json()
}

export async function undoSynergyDecision(pairId) {
  const res = await fetch(`${BASE}/synergy/pairs/${pairId}/undo`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to undo synergy decision')
  return res.json()
}

export async function getSynergyGaps() {
  const res = await fetch(`${BASE}/synergy/gaps`)
  if (!res.ok) throw new Error('Failed to fetch synergy gaps')
  return res.json()
}

export async function detectSynergyGaps(force = false) {
  const res = await fetch(`${BASE}/synergy/gaps/detect?force=${force}`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to detect synergy gaps')
  return res.json()
}

export async function huntSynergyGap(gapId) {
  const res = await fetch(`${BASE}/synergy/gaps/${gapId}/hunt`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to hunt gap candidates')
  return res.json()
}

export async function shortlistAction(gapId, shortlistId, action) {
  const res = await fetch(`${BASE}/synergy/gaps/${gapId}/shortlist/${shortlistId}/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  })
  if (!res.ok) throw new Error('Failed to perform shortlist action')
  return res.json()
}

export async function dismissGap(gapId) {
  const res = await fetch(`${BASE}/synergy/gaps/${gapId}/dismiss`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to dismiss gap')
  return res.json()
}

export async function getCompanySummary(companyName) {
  const res = await fetch(`${BASE}/synergy/company/${encodeURIComponent(companyName)}/summary`)
  if (!res.ok) throw new Error('Failed to fetch company synergy summary')
  return res.json()
}
