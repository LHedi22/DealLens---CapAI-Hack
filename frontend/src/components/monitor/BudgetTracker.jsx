const CATEGORY_LABELS = {
  rd: 'R&D', construction: 'Construction', equipment: 'Equipment',
  salaries: 'Salaries', working_capital: 'Working Capital',
  marketing: 'Marketing', training: 'Training', other: 'Other',
}

const STATUS_CONFIG = {
  ON_TRACK:    { color: '#12B76A', badgeBg: 'rgba(18,183,106,0.10)',  badgeBorder: 'rgba(18,183,106,0.25)' },
  WARNING:     { color: '#D97706', badgeBg: 'rgba(245,165,36,0.10)',  badgeBorder: 'rgba(245,165,36,0.25)' },
  CRITICAL:    { color: '#DC2626', badgeBg: 'rgba(240,68,56,0.10)',   badgeBorder: 'rgba(240,68,56,0.25)'  },
  OVER_BUDGET: { color: '#DC2626', badgeBg: 'rgba(240,68,56,0.10)',   badgeBorder: 'rgba(240,68,56,0.25)'  },
  OFF_PLAN:    { color: '#DC2626', badgeBg: 'rgba(240,68,56,0.10)',   badgeBorder: 'rgba(240,68,56,0.25)'  },
}

const CARD = {
  background:   'var(--surface-1)',
  border:       '1px solid var(--border)',
  borderRadius: 14,
  padding:      '14px 16px',
  boxShadow:    '0 1px 3px rgba(16,24,40,0.06)',
}

function fmt(n) {
  if (n == null) return '—'
  return n.toLocaleString('fr-TN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function VarianceArrow({ pct, status }) {
  if (pct == null) return <span style={{ color: 'var(--tx-3)' }}>—</span>
  const cfg   = STATUS_CONFIG[status] || STATUS_CONFIG.ON_TRACK
  const arrow = pct > 0 ? '↑' : pct < 0 ? '↓' : '→'
  return (
    <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: cfg.color, fontWeight: 600 }}>
      {arrow} {Math.abs(pct).toFixed(1)}%
    </span>
  )
}

export default function BudgetTracker({ categoryTotals }) {
  if (!categoryTotals || Object.keys(categoryTotals).length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--tx-3)', fontSize: 13 }}>
        No category data available yet.
      </div>
    )
  }

  const entries = Object.entries(categoryTotals).sort((a, b) => {
    const order = { OVER_BUDGET: 0, CRITICAL: 1, OFF_PLAN: 2, WARNING: 3, ON_TRACK: 4 }
    return (order[a[1].status] ?? 5) - (order[b[1].status] ?? 5)
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {entries.map(([cat, data]) => {
        const { planned_tnd, spent_tnd, planned_to_date_tnd, variance_pct, status } = data
        const cfg    = STATUS_CONFIG[status] || STATUS_CONFIG.ON_TRACK
        const barMax = Math.max(planned_tnd || 0, spent_tnd || 0, 1)
        const barPct = Math.min(100, ((spent_tnd || 0) / barMax) * 100)
        const planPct = Math.min(100, ((planned_to_date_tnd || 0) / barMax) * 100)

        return (
          <div key={cat} style={CARD}>
            {/* Header row */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 10 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--tx-1)' }}>
                {CATEGORY_LABELS[cat] || cat}
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <VarianceArrow pct={variance_pct} status={status} />
                <span style={{
                  fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 5,
                  background: cfg.badgeBg, color: cfg.color,
                  border: `1px solid ${cfg.badgeBorder}`,
                  fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.04em',
                }}>
                  {status.replace('_', ' ')}
                </span>
              </div>
            </div>

            {/* Progress bar */}
            <div style={{ position: 'relative', height: 8, background: 'var(--surface-3)', borderRadius: 4, overflow: 'visible', marginBottom: 8 }}>
              {planned_to_date_tnd > 0 && (
                <div
                  style={{
                    position: 'absolute', top: 0, width: 1, height: '100%',
                    background: 'rgba(61,71,84,0.4)', zIndex: 10,
                    left: `${planPct}%`,
                  }}
                  title={`Expected by now: ${fmt(planned_to_date_tnd)} TND`}
                />
              )}
              <div style={{
                height: '100%', borderRadius: 4,
                width: `${barPct}%`, background: cfg.color,
                transition: 'width 0.5s',
              }} />
            </div>

            {/* Numbers */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 11, color: 'var(--tx-3)' }}>
              <span>
                <span>Spent </span>
                <span style={{ color: 'var(--tx-1)', fontWeight: 600, fontFamily: 'JetBrains Mono, monospace' }}>
                  {fmt(spent_tnd)} TND
                </span>
              </span>
              <span>
                <span>Planned </span>
                <span style={{ color: 'var(--tx-2)', fontFamily: 'JetBrains Mono, monospace' }}>
                  {fmt(planned_tnd)} TND
                </span>
              </span>
              {planned_to_date_tnd > 0 && (
                <span>
                  <span>Expected now </span>
                  <span style={{ color: 'var(--tx-2)', fontFamily: 'JetBrains Mono, monospace' }}>
                    {fmt(planned_to_date_tnd)} TND
                  </span>
                </span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
