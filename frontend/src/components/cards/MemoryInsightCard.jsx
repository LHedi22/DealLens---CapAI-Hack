import { motion } from 'framer-motion'

const DECISION_COLORS = {
  pursue:    { color: 'var(--s-green)',  bg: 'rgba(18,183,106,0.08)',   border: 'rgba(18,183,106,0.25)'   },
  watch:     { color: 'var(--s-amber)',  bg: 'rgba(245,165,36,0.08)',   border: 'rgba(245,165,36,0.25)'   },
  soft_pass: { color: 'var(--s-orange)', bg: 'rgba(239,104,32,0.08)',   border: 'rgba(239,104,32,0.25)'   },
  pass:      { color: 'var(--s-red)',    bg: 'rgba(240,68,56,0.08)',    border: 'rgba(240,68,56,0.25)'    },
}

const TREND_COLOR = { improving: 'var(--s-green)', declining: 'var(--s-red)', stable: 'var(--tx-3)' }
const TREND_ICON  = { improving: '↑', declining: '↓', stable: '→' }

const CARD    = { background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 20, padding: 28 }
const DIVIDER = { height: 1, background: 'var(--border)', margin: '20px 0' }
const SEC_LABEL = {
  fontSize: 10, fontWeight: 500, color: 'var(--tx-3)',
  letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 12, display: 'block',
}

function outcomeColor(outcome) {
  if (!outcome) return 'var(--tx-3)'
  const o = outcome.toLowerCase()
  if (o.includes('acquired') || o.includes('performing')) return 'var(--s-green)'
  if (o.includes('failed')   || o.includes('stalled'))    return 'var(--s-red)'
  return 'var(--tx-3)'
}

function MatchRow({ match, index }) {
  const dc = DECISION_COLORS[match.decision] || {
    color: 'var(--tx-2)', bg: 'rgba(16,19,24,0.05)', border: 'rgba(16,19,24,0.12)',
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.08 * index, duration: 0.3 }}
      style={{
        background:   'rgba(16,19,24,0.03)',
        border:       '1px solid var(--border)',
        borderRadius: 12,
        padding:      14,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontWeight: 700,
            fontSize:   13,
            color:      'var(--gold)',
            flexShrink: 0,
            minWidth:   42,
          }}
        >
          {match.similarity_pct}%
        </span>
        <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--tx-1)' }}>{match.startup_name}</span>
        <span style={{ color: 'var(--tx-3)', fontSize: 12 }}>·</span>
        <span style={{ fontSize: 12, color: 'var(--tx-2)' }}>{match.sector}</span>
        <span style={{ color: 'var(--tx-3)', fontSize: 12 }}>·</span>
        <span style={{ fontSize: 12, color: 'var(--tx-2)' }}>{match.stage}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, paddingLeft: 50 }}>
        <span
          style={{
            fontSize: 10, fontWeight: 600,
            padding: '2px 8px', borderRadius: 5,
            color: dc.color, background: dc.bg, border: `1px solid ${dc.border}`,
            fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.05em', textTransform: 'uppercase',
          }}
        >
          {match.decision}
        </span>
        <span style={{ fontSize: 12, color: 'var(--tx-3)' }}>→</span>
        <span style={{ fontSize: 12, fontWeight: 500, color: outcomeColor(match.outcome) }}>
          {match.outcome || 'Outcome unknown'}
        </span>
      </div>
    </motion.div>
  )
}

function SectorConviction({ data }) {
  if (!data?.sector) return null
  const icon  = TREND_ICON[data.trend_direction]  || '→'
  const color = TREND_COLOR[data.trend_direction] || 'var(--tx-3)'

  return (
    <div>
      <span style={SEC_LABEL}>Sector Conviction — {data.sector}</span>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20, marginBottom: 10 }}>
        {[
          { val: data.total_evaluations, label: `eval${data.total_evaluations !== 1 ? 's' : ''}` },
          data.total_evaluations > 0 && { val: data.total_pursued, label: 'pursued' },
          data.total_evaluations > 0 && { val: `${data.win_rate}%`, label: 'win rate' },
        ].filter(Boolean).map(({ val, label }) => (
          <span key={label} style={{ fontSize: 13, color: 'var(--tx-2)' }}>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: 'var(--tx-1)' }}>{val}</span>
            <span style={{ color: 'var(--tx-3)', marginLeft: 5, fontSize: 12 }}>{label}</span>
          </span>
        ))}
        {data.total_evaluations > 0 && (
          <span style={{ fontSize: 13, fontWeight: 600, color }}>{icon} {data.trend_direction}</span>
        )}
      </div>
      {data.learning_note && (
        <p style={{ fontSize: 12, color: 'var(--tx-2)', lineHeight: 1.6, margin: 0 }}>{data.learning_note}</p>
      )}
    </div>
  )
}

export default function MemoryInsightCard({ memoryData }) {
  if (!memoryData) return null

  const {
    conviction_delta   = 0,
    delta_explanation  = '',
    top_memory_matches = [],
    sector_conviction  = {},
  } = memoryData

  const deltaColor =
    conviction_delta > 0 ? 'var(--s-green)' :
    conviction_delta < 0 ? 'var(--s-red)'   : 'var(--tx-3)'
  const deltaSign = conviction_delta > 0 ? '+' : ''

  return (
    <motion.div
      style={CARD}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2, duration: 0.4 }}
    >
      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2
          style={{
            fontFamily: 'Outfit, Inter, system-ui, sans-serif',
            fontSize: 22, fontWeight: 700,
            color: 'var(--tx-1)', margin: 0, letterSpacing: '-0.01em',
          }}
        >
          Memory Insight
        </h2>
        <span style={{ fontSize: 11, color: 'var(--tx-3)', fontFamily: 'JetBrains Mono, monospace' }}>
          {top_memory_matches.length} similar deal{top_memory_matches.length !== 1 ? 's' : ''} found
        </span>
      </div>

      <div style={{ height: 1, background: 'var(--border)', margin: '20px 0' }} />

      {/* ── Conviction Delta ── */}
      <div>
        <span style={SEC_LABEL}>Conviction Delta</span>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 12 }}>
          <span
            style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: 48, fontWeight: 700,
              letterSpacing: '-0.04em', lineHeight: 1,
              color: deltaColor,
            }}
          >
            {deltaSign}{conviction_delta}
          </span>
          <span style={{ fontSize: 13, color: 'var(--tx-3)' }}>pts</span>
        </div>
        {delta_explanation && (
          <div
            style={{
              borderLeft: '2px solid var(--gold)',
              paddingLeft: 14,
              fontSize: 13,
              color: 'var(--tx-2)',
              lineHeight: 1.6,
            }}
          >
            {delta_explanation}
          </div>
        )}
      </div>

      {/* ── Similar Past Deals ── */}
      {top_memory_matches.length > 0 && (
        <>
          <div style={DIVIDER} />
          <span style={SEC_LABEL}>Similar Past Deals</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {top_memory_matches.map((match, i) => (
              <MatchRow key={match.startup_name} match={match} index={i} />
            ))}
          </div>
        </>
      )}

      {/* ── Sector Conviction ── */}
      {sector_conviction?.sector && (
        <>
          <div style={DIVIDER} />
          <SectorConviction data={sector_conviction} />
        </>
      )}
    </motion.div>
  )
}
