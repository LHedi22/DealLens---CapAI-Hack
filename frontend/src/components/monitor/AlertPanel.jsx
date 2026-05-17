import { useState, useEffect, useCallback } from 'react'
import { getMonitorAlerts, resolveMonitorAlert } from '../../lib/api'

const SEVERITY_STYLE = {
  CRITICAL: { bg: 'rgba(240,68,56,0.10)', color: '#991B1B', border: 'rgba(240,68,56,0.30)' },
  WARNING:  { bg: 'rgba(245,165,36,0.10)', color: '#92400E', border: 'rgba(245,165,36,0.30)' },
}

const TYPE_LABELS = {
  OFF_PLAN:              'Off-Plan Spend',
  OVER_BUDGET:           'Over Budget',
  LARGE_UNKNOWN:         'Large Unknown',
  REPEATED_UNCLASSIFIED: 'Repeated Unclassified',
  ROUND_LARGE:           'Round Large Payment',
  PACE_WARNING:          'Pace Warning',
  NO_STATEMENT:          'No Statement',
  ZERO_ACTIVITY:         'Zero Activity',
  UNCLASSIFIED:          'Unclassified',
}

const CARD = {
  background:   'var(--surface-1)',
  border:       '1px solid var(--border)',
  borderRadius: 14,
  padding:      16,
  boxShadow:    '0 1px 3px rgba(16,24,40,0.06)',
}

function AlertCard({ alert, onResolved }) {
  const [open, setOpen]     = useState(false)
  const [note, setNote]     = useState('')
  const [saving, setSaving] = useState(false)

  async function handleResolve() {
    setSaving(true)
    try {
      await resolveMonitorAlert(alert.id, note)
      onResolved(alert.id)
    } catch {
      // ignore
    } finally {
      setSaving(false)
      setOpen(false)
    }
  }

  const sev = SEVERITY_STYLE[alert.severity] || SEVERITY_STYLE.WARNING

  return (
    <div style={{
      background:   alert.severity === 'CRITICAL' ? 'rgba(240,68,56,0.04)' : 'rgba(245,165,36,0.04)',
      border:       `1px solid ${alert.severity === 'CRITICAL' ? 'rgba(240,68,56,0.18)' : 'rgba(245,165,36,0.18)'}`,
      borderRadius: 14,
      padding:      16,
      display:      'flex',
      flexDirection:'column',
      gap:          10,
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        {/* Severity pill */}
        <span style={{
          fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 5,
          background: sev.bg, color: sev.color, border: `1px solid ${sev.border}`,
          flexShrink: 0, marginTop: 1, fontFamily: 'JetBrains Mono, monospace',
          letterSpacing: '0.04em',
        }}>
          {alert.severity}
        </span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--tx-1)' }}>
              {TYPE_LABELS[alert.alert_type] || alert.alert_type}
            </span>
            <span style={{ fontSize: 10, color: 'var(--tx-3)', flexShrink: 0, fontFamily: 'JetBrains Mono, monospace' }}>
              {alert.fired_at ? alert.fired_at.slice(0, 10) : '—'}
            </span>
          </div>
          <p style={{ fontSize: 12, color: 'var(--tx-2)', margin: '4px 0 0', lineHeight: 1.5 }}>
            {alert.alert_summary}
          </p>
          {alert.alert_detail && (
            <p style={{ fontSize: 12, color: 'var(--tx-3)', margin: '4px 0 0', lineHeight: 1.5 }}>
              {alert.alert_detail}
            </p>
          )}
        </div>
      </div>

      {!alert.resolved && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 2 }}>
          {!open ? (
            <button
              onClick={() => setOpen(true)}
              style={{
                fontSize: 12, padding: '5px 12px', borderRadius: 8,
                background: 'var(--surface-2)', color: 'var(--tx-2)',
                border: '1px solid var(--border)', cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              Resolve
            </button>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, width: '100%' }}>
              <textarea
                value={note}
                onChange={e => setNote(e.target.value)}
                placeholder="Resolution note (optional)…"
                rows={2}
                style={{
                  width: '100%', fontSize: 12, resize: 'none',
                  background: 'var(--surface-1)', border: '1px solid var(--border)',
                  borderRadius: 8, padding: '8px 10px', color: 'var(--tx-1)',
                  fontFamily: 'Inter, system-ui, sans-serif',
                }}
              />
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <button
                  onClick={() => { setOpen(false); setNote('') }}
                  style={{
                    fontSize: 12, padding: '5px 12px', borderRadius: 8,
                    background: 'var(--surface-2)', color: 'var(--tx-2)',
                    border: '1px solid var(--border)', cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleResolve}
                  disabled={saving}
                  style={{
                    fontSize: 12, padding: '5px 12px', borderRadius: 8,
                    background: '#12B76A', color: '#FFFFFF',
                    border: 'none', cursor: saving ? 'not-allowed' : 'pointer',
                    opacity: saving ? 0.6 : 1,
                  }}
                >
                  {saving ? 'Saving…' : 'Confirm resolve'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {alert.resolved && alert.resolved_by_note && (
        <p style={{
          fontSize: 11, color: 'var(--tx-3)', fontStyle: 'italic',
          borderTop: '1px solid var(--border)', paddingTop: 8, margin: 0,
        }}>
          Resolved: {alert.resolved_by_note}
        </p>
      )}
    </div>
  )
}

export default function AlertPanel({ startupName, onHealthChanged }) {
  const [alerts, setAlerts]             = useState([])
  const [loading, setLoading]           = useState(false)
  const [showResolved, setShowResolved] = useState(false)

  const load = useCallback(async () => {
    if (!startupName) return
    setLoading(true)
    try {
      const data = await getMonitorAlerts(startupName)
      setAlerts(data.alerts || [])
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [startupName])

  useEffect(() => { load() }, [load])

  function handleResolved(alertId) {
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, resolved: true } : a))
    if (onHealthChanged) onHealthChanged()
  }

  const active = alerts.filter(a => !a.resolved).sort((a, b) => {
    if (a.severity === 'CRITICAL' && b.severity !== 'CRITICAL') return -1
    if (b.severity === 'CRITICAL' && a.severity !== 'CRITICAL') return 1
    return 0
  })
  const resolved = alerts.filter(a => a.resolved)

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--tx-3)', fontSize: 13 }}>
        Loading alerts…
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* Active alerts */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <h3 style={{
          fontSize: 10, fontWeight: 600, color: 'var(--tx-3)',
          textTransform: 'uppercase', letterSpacing: '0.10em', margin: 0,
        }}>
          Active Alerts ({active.length})
        </h3>
        {active.length === 0 ? (
          <div style={{
            textAlign: 'center', padding: '32px 0', fontSize: 13, color: 'var(--tx-3)',
            background: 'var(--surface-2)', borderRadius: 12, border: '1px solid var(--border)',
          }}>
            No active alerts — all clear.
          </div>
        ) : (
          active.map(a => <AlertCard key={a.id} alert={a} onResolved={handleResolved} />)
        )}
      </div>

      {/* Resolved (collapsible) */}
      {resolved.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <button
            onClick={() => setShowResolved(v => !v)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              fontSize: 10, fontWeight: 600, color: 'var(--tx-3)',
              textTransform: 'uppercase', letterSpacing: '0.10em',
              background: 'none', border: 'none', cursor: 'pointer',
              transition: 'color 0.15s',
            }}
          >
            <span>{showResolved ? '▾' : '▸'}</span>
            Resolved ({resolved.length})
          </button>
          {showResolved && resolved.map(a => (
            <div key={a.id} style={{ opacity: 0.55 }}>
              <AlertCard alert={a} onResolved={() => {}} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
