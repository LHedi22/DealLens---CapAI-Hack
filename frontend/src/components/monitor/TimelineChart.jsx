import { useState, useEffect } from 'react'
import {
  ComposedChart, Bar, Line, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { getMonitorTimeline } from '../../lib/api'

function fmt(n) {
  if (n == null) return '—'
  return Number(n).toLocaleString('fr-TN', { maximumFractionDigits: 0 }) + ' TND'
}

function SpendTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-900 border border-slate-700 rounded p-3 text-xs shadow-lg">
      <p className="text-slate-400 mb-2 font-medium">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }} className="leading-relaxed">
          {p.name}: {fmt(p.value)}
        </p>
      ))}
    </div>
  )
}

function HealthTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const score = payload[0]?.value
  const color = score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : score >= 25 ? '#f97316' : '#ef4444'
  return (
    <div className="bg-slate-900 border border-slate-700 rounded p-3 text-xs shadow-lg">
      <p className="text-slate-400 mb-1 font-medium">{label}</p>
      <p style={{ color }}>Health: {score ?? '—'} / 100</p>
    </div>
  )
}

function EmptyState({ message, sub }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-2 text-slate-500">
      <p className="text-base font-medium text-slate-400">{message}</p>
      {sub && <p className="text-sm">{sub}</p>}
    </div>
  )
}

export default function TimelineChart({ startupName }) {
  const [data, setData]     = useState(null)
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
      <div className="flex items-center justify-center py-16 text-slate-400 text-sm">
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

  // ── Monthly bar chart data: actual spend per month + plan rate reference ──
  const barData = monthly_spending.map(row => ({
    month: row.month,
    'Actual Spend': row.spent_tnd,
    'Monthly Plan Rate': monthly_plan_rate_tnd,
  }))

  // ── Cumulative + health data from snapshots ───────────────────────────────
  const cumulData = snapshots.map(s => ({
    month: s.month,
    'Actual (cumulative)': s.total_spent_tnd,
    'Planned pace': s.total_planned_to_date_tnd,
    health: s.compliance_health_score,
    alerts: s.alert_count_active,
  }))

  const tickFmt = v => v >= 1_000_000
    ? `${(v / 1_000_000).toFixed(1)}M`
    : v >= 1_000
    ? `${(v / 1_000).toFixed(0)}K`
    : v

  return (
    <div className="flex flex-col gap-6">

      {/* ── Summary row ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total Committed', value: fmt(total_committed_tnd) },
          { label: 'Agreement Duration', value: `${agreement_duration_months} months` },
          { label: 'Monthly Plan Rate', value: fmt(monthly_plan_rate_tnd) },
        ].map(({ label, value }) => (
          <div key={label} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <p className="text-xs text-slate-400 uppercase tracking-wide">{label}</p>
            <p className="text-lg font-semibold text-white mt-1">{value}</p>
          </div>
        ))}
      </div>

      {/* ── Monthly spend bars ───────────────────────────────────────────── */}
      {barData.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
          <h3 className="text-sm font-medium text-slate-300 mb-4">Monthly Spending vs Plan Rate</h3>
          <ResponsiveContainer width="100%" height={220}>
            <ComposedChart data={barData} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={tickFmt} width={52} />
              <Tooltip content={<SpendTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8', paddingTop: 8 }} />
              <Bar dataKey="Actual Spend" fill="#6366f1" radius={[4, 4, 0, 0]} maxBarSize={60} />
              <Line
                type="monotone"
                dataKey="Monthly Plan Rate"
                stroke="#22c55e"
                strokeDasharray="5 5"
                strokeWidth={2}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ── Cumulative area chart ─────────────────────────────────────────── */}
      {cumulData.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
          <h3 className="text-sm font-medium text-slate-300 mb-4">Cumulative Spending vs Planned Pace</h3>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={cumulData} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={tickFmt} width={52} />
              <Tooltip content={<SpendTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8', paddingTop: 8 }} />
              <Area
                type="monotone"
                dataKey="Actual (cumulative)"
                stroke="#6366f1"
                fill="#6366f130"
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="Planned pace"
                stroke="#22c55e"
                fill="#22c55e15"
                strokeWidth={2}
                strokeDasharray="5 5"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ── Health score trend ────────────────────────────────────────────── */}
      {cumulData.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
          <h3 className="text-sm font-medium text-slate-300 mb-4">Compliance Health Score Over Time</h3>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={cumulData} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} width={36} />
              <Tooltip content={<HealthTooltip />} />
              <ReferenceLine y={75} stroke="#22c55e55" strokeDasharray="4 4" label={{ value: '75', position: 'right', fill: '#22c55e', fontSize: 10 }} />
              <ReferenceLine y={50} stroke="#f59e0b55" strokeDasharray="4 4" label={{ value: '50', position: 'right', fill: '#f59e0b', fontSize: 10 }} />
              <ReferenceLine y={25} stroke="#ef444455" strokeDasharray="4 4" label={{ value: '25', position: 'right', fill: '#ef4444', fontSize: 10 }} />
              <Line
                type="monotone"
                dataKey="health"
                name="Health Score"
                stroke="#818cf8"
                strokeWidth={2.5}
                dot={{ fill: '#818cf8', r: 5, strokeWidth: 0 }}
                activeDot={{ r: 7 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
          <p className="text-[10px] text-slate-600 mt-2 text-right">
            Reference lines: 75 = Good · 50 = Watch · 25 = Critical
          </p>
        </div>
      )}
    </div>
  )
}
