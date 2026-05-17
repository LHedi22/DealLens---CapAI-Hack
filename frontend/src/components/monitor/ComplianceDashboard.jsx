import ComplianceHealthBadge from './ComplianceHealthBadge'

const STATUS_COLOR = {
  ON_TRACK:    '#12B76A',
  WARNING:     '#F5A524',
  CRITICAL:    '#EF6820',
  OVER_BUDGET: '#F04438',
  OFF_PLAN:    '#F04438',
}

const STATUS_LABEL = {
  ON_TRACK:    'ON TRACK',
  WARNING:     'WARNING',
  CRITICAL:    'CRITICAL',
  OVER_BUDGET: 'OVER BUDGET',
  OFF_PLAN:    'OFF PLAN',
}

const CARD = {
  background:   'var(--surface-1)',
  border:       '1px solid var(--border)',
  borderRadius: 16,
  padding:      '16px 20px',
  boxShadow:    '0 1px 3px rgba(16,24,40,0.06)',
}

function fmt(n) {
  if (n == null) return '—'
  return Number(n).toLocaleString('fr-TN')
}

function StatCard({ label, value, sub }) {
  return (
    <div style={CARD}>
      <p style={{ fontSize: 10, color: 'var(--tx-3)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 500, margin: 0 }}>
        {label}
      </p>
      <p style={{ fontSize: 22, fontWeight: 700, color: 'var(--tx-1)', margin: '6px 0 0', letterSpacing: '-0.02em', fontFamily: 'JetBrains Mono, monospace' }}>
        {value}
      </p>
      {sub && <p style={{ fontSize: 11, color: 'var(--tx-3)', margin: '3px 0 0' }}>{sub}</p>}
    </div>
  )
}

function MiniBudgetRow({ name, data }) {
  const color = STATUS_COLOR[data.status] ?? '#64748B'
  const pct = data.planned_tnd > 0
    ? Math.min((data.spent_tnd / data.planned_tnd) * 100, 130)
    : data.spent_tnd > 0 ? 100 : 0
  const varSign = data.variance_pct != null && data.variance_pct > 0 ? '+' : ''
  const varText = data.variance_pct != null
    ? `${varSign}${data.variance_pct.toFixed(1)}%`
    : 'OFF-PLAN'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            fontSize: 10, fontWeight: 600, padding: '2px 6px', borderRadius: 5,
            background: `${color}18`, color, border: `1px solid ${color}44`,
          }}>
            {STATUS_LABEL[data.status] ?? data.status}
          </span>
          <span style={{ color: 'var(--tx-2)', textTransform: 'capitalize' }}>
            {name.replace(/_/g, ' ')}
          </span>
        </div>
        <span style={{ fontWeight: 600, color, fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>
          {varText}
        </span>
      </div>
      <div style={{ height: 6, background: 'var(--surface-3)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{
          height: '100%', borderRadius: 3,
          width: `${Math.min(pct, 100)}%`,
          background: color,
          transition: 'width 0.5s',
        }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--tx-3)', fontFamily: 'JetBrains Mono, monospace' }}>
        <span>{fmt(data.spent_tnd)} TND spent</span>
        <span>{fmt(data.planned_tnd)} TND allocated</span>
      </div>
    </div>
  )
}

export default function ComplianceDashboard({ dashboard }) {
  if (!dashboard) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '64px 0', color: 'var(--tx-3)', fontSize: 13 }}>
        Loading dashboard…
      </div>
    )
  }

  if (!dashboard.has_agreement) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '64px 0', gap: 8 }}>
        <p style={{ fontSize: 15, fontWeight: 600, color: 'var(--tx-2)', margin: 0 }}>No investment agreement on file</p>
        <p style={{ fontSize: 13, color: 'var(--tx-3)', margin: 0 }}>Upload a signed SICAR agreement to begin monitoring.</p>
      </div>
    )
  }

  const { total_committed_tnd, total_spent_tnd, months_elapsed,
          agreement_duration_months, compliance_health_score, category_totals,
          unclassified_tnd } = dashboard

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14 }}>
        <StatCard
          label="Total Committed"
          value={`${fmt(total_committed_tnd)} TND`}
          sub="SICAR agreement total"
        />
        <StatCard
          label="Total Spent"
          value={`${fmt(total_spent_tnd)} TND`}
          sub={unclassified_tnd > 0 ? `incl. ${fmt(unclassified_tnd)} TND unclassified` : 'all classified'}
        />
        <StatCard
          label="Months Elapsed"
          value={`${months_elapsed ?? '—'} of ${agreement_duration_months}`}
          sub={months_elapsed ? `${agreement_duration_months - months_elapsed} months remaining` : null}
        />
      </div>

      {/* Health badge */}
      <div style={{
        ...CARD,
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, padding: '24px',
      }}>
        <p style={{ fontSize: 10, color: 'var(--tx-3)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 500, margin: 0 }}>
          Compliance Health Score
        </p>
        <ComplianceHealthBadge score={compliance_health_score} />
      </div>

      {/* Mini budget tracker */}
      {category_totals && Object.keys(category_totals).length > 0 && (
        <div style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--tx-1)', margin: 0 }}>Budget by Category</h3>
          {Object.entries(category_totals).map(([name, data]) => (
            <MiniBudgetRow key={name} name={name} data={data} />
          ))}
        </div>
      )}
    </div>
  )
}
