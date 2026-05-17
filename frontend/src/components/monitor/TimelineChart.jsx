import { useState, useEffect } from 'react'
import {
  ComposedChart, Bar, Line, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { getMonitorTimeline } from '../../lib/api'

const CHART_CARD = {
  background:   'var(--surface-1)',
  border:       '1px solid var(--border)',
  borderRadius: 16,
  padding:      20,
  boxShadow:    '0 1px 3px rgba(16,24,40,0.06)',
}

const STAT_CARD = {
  background:   'var(--surface-1)',
  border:       '1px solid var(--border)',
  borderRadius: 14,
  padding:      '14px 18px',
  boxShadow:    '0 1px 3px rgba(16,24,40,0.06)',
}

function fmt(n) {
  if (n == null) return '—'
  return Number(n).toLocaleString('fr-TN', { maximumFractionDigits: 0 }) + ' TND'
}

function SpendTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--surface-1)', border: '1px solid var(--border)',
      borderRadius: 10, padding: '10px 14px', fontSize: 12,
      boxShadow: '0 4px 16px rgba(16,24,40,0.10)',
    }}>
      <p style={{ color: 'var(--tx-2)', marginBottom: 6, fontWeight: 600 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color, margin: '2px 0', lineHeight: 1.5 }}>
          {p.name}: {fmt(p.value)}
        </p>
      ))}
    </div>
  )
}

function HealthTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const score = payload[0]?.value
  const color = score >= 75 ? '#12B76A' : score >= 50 ? '#F5A524' : score >= 25 ? '#EF6820' : '#F04438'
  return (
    <div style={{
      background: 'var(--surface-1)', border: '1px solid var(--border)',
      borderRadius: 10, padding: '10px 14px', fontSize: 12,
      boxShadow: '0 4px 16px rgba(16,24,40,0.10)',
    }}>
      <p style={{ color: 'var(--tx-2)', marginBottom: 4, fontWeight: 600 }}>{label}</p>
      <p style={{ color, margin: 0 }}>Health: {score ?? '—'} / 100</p>
    </div>
  )
}

function EmptyState({ message, sub }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '64px 0', gap: 8 }}>
      <p style={{ fontSize: 15, fontWeight: 600, color: 'var(--tx-2)', margin: 0 }}>{message}</p>
      {sub && <p style={{ fontSize: 13, color: 'var(--tx-3)', margin: 0 }}>{sub}</p>}
    </div>
  )
}

const AXIS_STYLE = { fill: '#64748B', fontSize: 11 }
const GRID_STROKE = '#E7E9EE'
const LEGEND_STYLE = { fontSize: 11, color: '#64748B', paddingTop: 8 }

export default function TimelineChart({ startupName }) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!startupName) return
    setLoading(true)
    setData(null)
    getMonitorTimeline(startupName)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [startupName])

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '64px 0', color: 'var(--tx-3)', fontSize: 13 }}>
        Loading timeline…
      </div>
    )
  }

  if (!data?.has_agreement) {
    return <EmptyState message="No investment agreement on file" sub="Upload a signed SICAR agreement to begin monitoring." />
  }

  const { monthly_spending, snapshots, monthly_plan_rate_tnd, total_committed_tnd, agreement_duration_months } = data

  if (!monthly_spending.length && !snapshots.length) {
    return <EmptyState message="No statements uploaded yet" sub="Upload bank statements to see the spending timeline." />
  }

  const barData = monthly_spending.map(row => ({
    month: row.month,
    'Actual Spend': row.spent_tnd,
    'Monthly Plan Rate': monthly_plan_rate_tnd,
  }))

  const cumulData = snapshots.map(s => ({
    month: s.month,
    'Actual (cumulative)': s.total_spent_tnd,
    'Planned pace': s.total_planned_to_date_tnd,
    health: s.compliance_health_score,
    alerts: s.alert_count_active,
  }))

  const tickFmt = v =>
    v >= 1_000_000 ? `${(v / 1_000_000).toFixed(1)}M` :
    v >= 1_000     ? `${(v / 1_000).toFixed(0)}K`     : v

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Summary row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14 }}>
        {[
          { label: 'Total Committed',     value: fmt(total_committed_tnd)        },
          { label: 'Agreement Duration',  value: `${agreement_duration_months} months` },
          { label: 'Monthly Plan Rate',   value: fmt(monthly_plan_rate_tnd)      },
        ].map(({ label, value }) => (
          <div key={label} style={STAT_CARD}>
            <p style={{ fontSize: 10, color: 'var(--tx-3)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 500, margin: 0 }}>
              {label}
            </p>
            <p style={{ fontSize: 20, fontWeight: 700, color: 'var(--tx-1)', margin: '6px 0 0', letterSpacing: '-0.02em', fontFamily: 'JetBrains Mono, monospace' }}>
              {value}
            </p>
          </div>
        ))}
      </div>

      {/* Monthly bars */}
      {barData.length > 0 && (
        <div style={CHART_CARD}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--tx-1)', margin: '0 0 16px' }}>
            Monthly Spending vs Plan Rate
          </h3>
          <ResponsiveContainer width="100%" height={220}>
            <ComposedChart data={barData} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
              <XAxis dataKey="month" tick={AXIS_STYLE} />
              <YAxis tick={AXIS_STYLE} tickFormatter={tickFmt} width={52} />
              <Tooltip content={<SpendTooltip />} />
              <Legend wrapperStyle={LEGEND_STYLE} />
              <Bar dataKey="Actual Spend" fill="#6E56CF" radius={[4, 4, 0, 0]} maxBarSize={60} />
              <Line type="monotone" dataKey="Monthly Plan Rate" stroke="#12B76A" strokeDasharray="5 5" strokeWidth={2} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Cumulative area */}
      {cumulData.length > 0 && (
        <div style={CHART_CARD}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--tx-1)', margin: '0 0 16px' }}>
            Cumulative Spending vs Planned Pace
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={cumulData} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
              <XAxis dataKey="month" tick={AXIS_STYLE} />
              <YAxis tick={AXIS_STYLE} tickFormatter={tickFmt} width={52} />
              <Tooltip content={<SpendTooltip />} />
              <Legend wrapperStyle={LEGEND_STYLE} />
              <Area type="monotone" dataKey="Actual (cumulative)" stroke="#6E56CF" fill="rgba(110,86,207,0.10)" strokeWidth={2} />
              <Area type="monotone" dataKey="Planned pace" stroke="#12B76A" fill="rgba(18,183,106,0.08)" strokeWidth={2} strokeDasharray="5 5" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Health score trend */}
      {cumulData.length > 0 && (
        <div style={CHART_CARD}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--tx-1)', margin: '0 0 16px' }}>
            Compliance Health Score Over Time
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={cumulData} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
              <XAxis dataKey="month" tick={AXIS_STYLE} />
              <YAxis domain={[0, 100]} tick={AXIS_STYLE} width={36} />
              <Tooltip content={<HealthTooltip />} />
              <ReferenceLine y={75} stroke="rgba(18,183,106,0.35)"  strokeDasharray="4 4" label={{ value: '75', position: 'right', fill: '#12B76A', fontSize: 10 }} />
              <ReferenceLine y={50} stroke="rgba(245,165,36,0.35)"  strokeDasharray="4 4" label={{ value: '50', position: 'right', fill: '#F5A524', fontSize: 10 }} />
              <ReferenceLine y={25} stroke="rgba(240,68,56,0.35)"   strokeDasharray="4 4" label={{ value: '25', position: 'right', fill: '#F04438', fontSize: 10 }} />
              <Line
                type="monotone" dataKey="health" name="Health Score"
                stroke="#6E56CF" strokeWidth={2.5}
                dot={{ fill: '#6E56CF', r: 5, strokeWidth: 0 }}
                activeDot={{ r: 7 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
          <p style={{ fontSize: 10, color: 'var(--tx-3)', marginTop: 8, textAlign: 'right' }}>
            Reference lines: 75 = Good · 50 = Watch · 25 = Critical
          </p>
        </div>
      )}
    </div>
  )
}
