import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import SynergyTypeBadge from './SynergyTypeBadge'
import SynergyScoreBar from './SynergyScoreBar'
import SynergyCard from './SynergyCard'

const FILTERS = [
  { key: 'all',      label: 'All' },
  { key: 'SERVICE',  label: 'Service Bridge' },
  { key: 'CUSTOMER', label: 'Shared Customer' },
  { key: 'CO_DEV',   label: 'Co-Dev' },
  { key: 'pending',  label: 'Pending Review' },
]

const DECISION_STYLE = {
  approved: { color: '#22c55e', label: 'Approved' },
  rejected: { color: '#ef4444', label: 'Rejected' },
  snoozed:  { color: '#94a3b8', label: 'Snoozed'  },
}

function scoreColor(s) {
  if (!s) return 'var(--tx-3)'
  if (s >= 75) return '#22c55e'
  if (s >= 60) return '#f59e0b'
  if (s >= 45) return '#f97316'
  return '#ef4444'
}

const TH = {
  padding: '10px 14px', textAlign: 'left',
  fontSize: 10, fontWeight: 600, color: 'var(--tx-3)',
  letterSpacing: '0.08em', textTransform: 'uppercase',
  borderBottom: '1px solid var(--border)',
  whiteSpace: 'nowrap',
}

const TD = {
  padding: '12px 14px',
  borderBottom: '1px solid var(--border)',
  verticalAlign: 'middle',
}

export default function SynergyPairTable({ pairs = [], onDecide, selectedPairId }) {
  const [filter, setFilter]     = useState('all')
  const [expandedId, setExpandedId] = useState(null)

  useEffect(() => {
    if (selectedPairId != null) setExpandedId(selectedPairId)
  }, [selectedPairId])

  const filtered = pairs.filter(p => {
    const types = p.synergy_types_triggered || []
    if (filter === 'pending')  return p.analyst_decision === null
    if (filter === 'all')      return true
    return types.includes(filter)
  })

  function toggleExpand(id) {
    setExpandedId(prev => (prev === id ? null : id))
  }

  return (
    <div>
      {/* ── Filter bar ── */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 18, flexWrap: 'wrap' }}>
        {FILTERS.map(f => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            style={{
              padding: '5px 14px', borderRadius: 8, fontSize: 12, fontWeight: 600,
              cursor: 'pointer', border: '1px solid',
              borderColor: filter === f.key ? '#6E56CF' : 'var(--border)',
              background:  filter === f.key ? 'rgba(110,86,207,0.1)' : 'transparent',
              color:       filter === f.key ? '#6E56CF' : 'var(--tx-2)',
              transition:  'all 0.15s',
            }}
          >
            {f.label}
            {f.key === 'pending' && (
              <span style={{ marginLeft: 6, background: 'rgba(110,86,207,0.15)', color: '#6E56CF', borderRadius: 10, padding: '1px 6px', fontSize: 10 }}>
                {pairs.filter(p => p.analyst_decision === null).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--tx-3)', fontSize: 13 }}>
          No pairs match this filter.
        </div>
      ) : (
        <div style={{ border: '1px solid var(--border)', borderRadius: 14, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'rgba(16,19,24,0.02)' }}>
                <th style={TH}>Company A</th>
                <th style={TH}>Company B</th>
                <th style={TH}>Types</th>
                <th style={{ ...TH, textAlign: 'right' }}>Score</th>
                <th style={TH}>Confidence</th>
                <th style={TH}>Value</th>
                <th style={{ ...TH, textAlign: 'right' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(pair => {
                const isExpanded = expandedId === pair.id
                const types      = pair.synergy_types_triggered || []
                const decStyle   = DECISION_STYLE[pair.analyst_decision]

                return [
                  <tr
                    key={pair.id}
                    onClick={() => toggleExpand(pair.id)}
                    style={{
                      cursor: 'pointer',
                      background: isExpanded ? 'rgba(110,86,207,0.04)' : 'transparent',
                      transition: 'background 0.15s',
                    }}
                    onMouseEnter={e => { if (!isExpanded) e.currentTarget.style.background = 'rgba(16,19,24,0.025)' }}
                    onMouseLeave={e => { if (!isExpanded) e.currentTarget.style.background = 'transparent' }}
                  >
                    <td style={TD}>
                      <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--tx-1)' }}>{pair.company_a}</span>
                    </td>
                    <td style={TD}>
                      <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--tx-1)' }}>{pair.company_b}</span>
                    </td>
                    <td style={TD}>
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {types.map(t => <SynergyTypeBadge key={t} type={t} small />)}
                      </div>
                    </td>
                    <td style={{ ...TD, textAlign: 'right' }}>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, fontSize: 15, color: scoreColor(pair.composite_score) }}>
                        {pair.composite_score}
                      </span>
                    </td>
                    <td style={TD}>
                      <span style={{ fontSize: 11, color: 'var(--tx-2)' }}>{pair.confidence_level}</span>
                    </td>
                    <td style={TD}>
                      <span style={{ fontSize: 11, color: 'var(--tx-2)', textTransform: 'capitalize' }}>
                        {(pair.value_creation_type || '').replace('_', ' ')}
                      </span>
                    </td>
                    <td style={{ ...TD, textAlign: 'right' }}>
                      {decStyle ? (
                        <span style={{ fontSize: 11, fontWeight: 600, color: decStyle.color }}>{decStyle.label}</span>
                      ) : (
                        <span style={{ fontSize: 10, fontWeight: 500, color: 'var(--tx-3)', padding: '2px 7px', borderRadius: 5, background: 'rgba(16,19,24,0.05)' }}>
                          Pending
                        </span>
                      )}
                    </td>
                  </tr>,
                  isExpanded && (
                    <tr key={`${pair.id}-detail`}>
                      <td colSpan={7} style={{ padding: '0 16px 16px', background: 'rgba(110,86,207,0.025)' }}>
                        <AnimatePresence>
                          <SynergyCard pair={pair} onDecide={onDecide} />
                        </AnimatePresence>
                      </td>
                    </tr>
                  ),
                ]
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
