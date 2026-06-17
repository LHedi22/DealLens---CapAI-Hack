import { useState } from 'react'
import { motion } from 'framer-motion'
import SynergyTypeBadge from './SynergyTypeBadge'
import SynergyScoreBar from './SynergyScoreBar'

const CONFIDENCE_COLORS = {
  HIGH:   { color: '#12B76A', bg: 'rgba(34,197,94,0.08)',   border: 'rgba(34,197,94,0.25)'   },
  MEDIUM: { color: '#F5A524', bg: 'rgba(245,158,11,0.08)',  border: 'rgba(245,158,11,0.25)'  },
  LOW:    { color: '#F04438', bg: 'rgba(239,68,68,0.08)',   border: 'rgba(239,68,68,0.25)'   },
}

const VALUE_META = {
  cost_saving:       { label: 'Cost Saving',      color: '#12B76A', bg: 'rgba(34,197,94,0.08)'   },
  revenue_expansion: { label: 'Revenue Expansion', color: '#3b82f6', bg: 'rgba(59,130,246,0.08)'  },
  new_market:        { label: 'New Market',        color: '#a855f7', bg: 'rgba(168,85,247,0.08)'  },
}

const DECISION_META = {
  approved: { label: 'Approved', color: '#12B76A', bg: 'rgba(34,197,94,0.08)',  border: 'rgba(34,197,94,0.25)'  },
  rejected: { label: 'Rejected', color: '#F04438', bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.25)'  },
  snoozed:  { label: 'Snoozed',  color: '#94a3b8', bg: 'rgba(148,163,184,0.08)', border: 'rgba(148,163,184,0.25)' },
}

function scoreColor(s) {
  if (s >= 75) return '#12B76A'
  if (s >= 60) return '#F5A524'
  if (s >= 45) return '#EF6820'
  return '#F04438'
}

const CARD    = { background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 20, padding: 28 }
const DIVIDER = { height: 1, background: 'var(--border)', margin: '20px 0' }
const SEC     = { fontSize: 10, fontWeight: 500, color: 'var(--tx-3)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 12, display: 'block' }

export default function SynergyCard({ pair, onDecide }) {
  const [decideMode, setDecideMode] = useState(null)
  const [reason, setReason] = useState('')

  if (!pair) return null

  const conf     = CONFIDENCE_COLORS[pair.confidence_level] || CONFIDENCE_COLORS.LOW
  const valMeta  = VALUE_META[pair.value_creation_type] || VALUE_META.cost_saving
  const decMeta  = pair.analyst_decision ? DECISION_META[pair.analyst_decision] : null
  const composite = pair.composite_score || 0
  const types    = pair.synergy_types_triggered || []

  function handleDecide(mode) {
    if (decideMode === mode) { setDecideMode(null); return }
    setDecideMode(mode)
    setReason('')
  }

  function submitDecide() {
    if (onDecide) onDecide(pair.id, { decision: decideMode, reason })
    setDecideMode(null)
    setReason('')
  }

  return (
    <motion.div
      style={CARD}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
        <div>
          <h3 style={{
            fontFamily: 'Outfit, Inter, system-ui, sans-serif',
            fontSize: 20, fontWeight: 700, color: 'var(--tx-1)',
            margin: '0 0 8px', letterSpacing: '-0.01em',
          }}>
            {pair.company_a}
            <span style={{ color: 'var(--tx-3)', margin: '0 10px', fontWeight: 300 }}>↔</span>
            {pair.company_b}
          </h3>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {types.map(t => <SynergyTypeBadge key={t} type={t} />)}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6, flexShrink: 0 }}>
          <span style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 28, fontWeight: 700, lineHeight: 1,
            color: scoreColor(composite),
          }}>
            {composite}
          </span>
          <div style={{ display: 'flex', gap: 6 }}>
            <span style={{ fontSize: 9, fontWeight: 600, padding: '2px 7px', borderRadius: 4, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.06em', textTransform: 'uppercase', background: conf.bg, color: conf.color, border: `1px solid ${conf.border}` }}>
              {pair.confidence_level}
            </span>
            {decMeta && (
              <span style={{ fontSize: 9, fontWeight: 600, padding: '2px 7px', borderRadius: 4, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.06em', textTransform: 'uppercase', background: decMeta.bg, color: decMeta.color, border: `1px solid ${decMeta.border}` }}>
                {decMeta.label}
              </span>
            )}
          </div>
        </div>
      </div>

      <div style={DIVIDER} />

      {/* ── Three Score Bars ── */}
      <span style={SEC}>Component Scores</span>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <SynergyScoreBar score={pair.service_bridge_score}  label="Service Bridge"  />
        <SynergyScoreBar score={pair.shared_customer_score} label="Shared Customer" />
        <SynergyScoreBar score={pair.co_dev_score}          label="Co-Development"  />
      </div>

      <div style={DIVIDER} />

      {/* ── Match Explanation ── */}
      <span style={SEC}>Match Explanation</span>
      <div style={{
        borderLeft: '2px solid var(--gold)', paddingLeft: 14,
        fontSize: 13, color: 'var(--tx-2)', lineHeight: 1.65,
      }}>
        {pair.match_explanation}
      </div>

      <div style={DIVIDER} />

      {/* ── Value + Action ── */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <div style={{ flex: 1, minWidth: 180 }}>
          <span style={SEC}>Value Creation</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ padding: '3px 9px', borderRadius: 6, fontSize: 11, fontWeight: 600, background: valMeta.bg, color: valMeta.color }}>
              {valMeta.label}
            </span>
            <span style={{ fontSize: 13, fontFamily: 'JetBrains Mono, monospace', color: 'var(--tx-1)', fontWeight: 600 }}>
              {pair.value_estimate_label}
            </span>
          </div>
        </div>
        <div style={{ flex: 1, minWidth: 200 }}>
          <span style={SEC}>Recommended Action</span>
          <p style={{ margin: 0, fontSize: 13, fontWeight: 600, color: 'var(--tx-1)', lineHeight: 1.5 }}>
            {pair.action_suggestion}
          </p>
        </div>
      </div>

      {/* ── Approve / Reject / Snooze ── */}
      {!pair.analyst_decision && (
        <>
          <div style={DIVIDER} />
          <div style={{ display: 'flex', gap: 8 }}>
            {[
              { mode: 'approved', label: 'Approve',  bg: '#12B76A', hoverBg: 'rgba(34,197,94,0.12)',  color: '#12B76A'  },
              { mode: 'rejected', label: 'Reject',   bg: '#F04438', hoverBg: 'rgba(239,68,68,0.12)', color: '#F04438'  },
              { mode: 'snoozed',  label: 'Snooze',   bg: '#94a3b8', hoverBg: 'rgba(148,163,184,0.12)', color: '#94a3b8' },
            ].map(({ mode, label, hoverBg, color }) => (
              <button
                key={mode}
                onClick={() => handleDecide(mode)}
                style={{
                  padding: '6px 14px', borderRadius: 8, fontSize: 12, fontWeight: 600,
                  cursor: 'pointer', border: `1px solid ${color}`,
                  background: decideMode === mode ? hoverBg : 'transparent',
                  color, transition: 'background 0.15s',
                }}
              >
                {label}
              </button>
            ))}
          </div>

          {decideMode && (
            <motion.div
              initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
              transition={{ duration: 0.2 }}
              style={{ marginTop: 12, overflow: 'hidden' }}
            >
              <textarea
                placeholder={`Reason for ${decideMode} (optional)…`}
                value={reason}
                onChange={e => setReason(e.target.value)}
                rows={2}
                style={{
                  width: '100%', boxSizing: 'border-box',
                  padding: '8px 12px', borderRadius: 8, fontSize: 13,
                  border: '1px solid var(--border)', background: 'var(--bg)',
                  color: 'var(--tx-1)', resize: 'vertical', fontFamily: 'inherit',
                  outline: 'none',
                }}
              />
              <button
                onClick={submitDecide}
                style={{
                  marginTop: 8, padding: '6px 16px', borderRadius: 8,
                  fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  background: '#6E56CF', color: '#fff', border: 'none',
                }}
              >
                Confirm {decideMode}
              </button>
            </motion.div>
          )}
        </>
      )}

      {/* ── Footer ── */}
      <div style={{ marginTop: 20 }}>
        <span style={{ fontSize: 10, color: 'var(--tx-3)', fontFamily: 'JetBrains Mono, monospace' }}>
          Last computed: {pair.created_at ? new Date(pair.created_at).toLocaleString() : '—'}
        </span>
      </div>
    </motion.div>
  )
}
