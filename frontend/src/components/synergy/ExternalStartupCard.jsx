import { useState } from 'react'

function fitColor(score) {
  if (score >= 75) return '#22c55e'
  if (score >= 60) return '#f59e0b'
  if (score >= 45) return '#f97316'
  return '#ef4444'
}

export default function ExternalStartupCard({ company, onAction }) {
  const [added,     setAdded]     = useState(company.analyst_action === 'add_to_pipeline')
  const [dismissed, setDismissed] = useState(company.analyst_action === 'dismissed')
  const [loading,   setLoading]   = useState(false)

  const color = fitColor(company.fit_score ?? 50)

  if (dismissed) return null

  async function handleAdd() {
    setLoading(true)
    try {
      await onAction(company.id, 'add_to_pipeline')
      setAdded(true)
    } finally {
      setLoading(false)
    }
  }

  async function handleDismiss() {
    setLoading(true)
    try {
      await onAction(company.id, 'dismissed')
      setDismissed(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      border: '1px solid var(--border)', borderRadius: 10,
      background: 'var(--bg)', padding: '12px 14px',
      display: 'flex', flexDirection: 'column', gap: 8,
      opacity: added ? 0.65 : 1, transition: 'opacity 0.2s',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
          <span style={{ fontWeight: 700, fontSize: 13, color: 'var(--tx-1)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {company.company_name}
          </span>
          {company.website && (
            <a
              href={company.website}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: 10, color: '#6E56CF', textDecoration: 'none', flexShrink: 0 }}
            >
              ↗
            </a>
          )}
        </div>
        <span style={{
          fontFamily: 'JetBrains Mono, monospace', fontSize: 16, fontWeight: 700,
          color, flexShrink: 0,
        }}>
          {company.fit_score ?? '—'}
        </span>
      </div>

      {/* Fit score bar — mandatory per spec */}
      <div style={{ height: 3, borderRadius: 3, background: 'rgba(16,19,24,0.06)', overflow: 'hidden' }}>
        <div style={{
          width: `${Math.min(100, Math.max(0, company.fit_score ?? 0))}%`,
          height: '100%', background: color, borderRadius: 3,
        }} />
      </div>

      {/* Fit reason */}
      {company.fit_reason && (
        <p style={{ margin: 0, fontSize: 11, color: 'var(--tx-2)', fontStyle: 'italic', lineHeight: 1.45 }}>
          {company.fit_reason}
        </p>
      )}

      {/* Flags */}
      {company.flags && company.flags.length > 0 && (
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {company.flags.map((f, i) => (
            <span key={i} style={{
              fontSize: 9, padding: '1px 6px', borderRadius: 4,
              background: 'rgba(245,158,11,0.08)', color: '#f59e0b',
              border: '1px solid rgba(245,158,11,0.2)',
              fontFamily: 'JetBrains Mono, monospace',
            }}>
              ⚠ {f}
            </span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 6 }}>
        {added ? (
          <span style={{ fontSize: 11, fontWeight: 600, color: '#22c55e', padding: '4px 0' }}>
            ✓ Added to Pipeline
          </span>
        ) : (
          <>
            <button
              onClick={handleAdd}
              disabled={loading}
              style={{
                flex: 1, padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                background: loading ? 'rgba(110,86,207,0.3)' : '#6E56CF',
                color: '#fff', border: 'none', transition: 'background 0.15s',
              }}
            >
              Add to Pipeline →
            </button>
            <button
              onClick={handleDismiss}
              disabled={loading}
              style={{
                padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                background: 'transparent', color: 'var(--tx-3)',
                border: '1px solid var(--border)', transition: 'all 0.15s',
              }}
            >
              Dismiss
            </button>
          </>
        )}
      </div>
    </div>
  )
}
