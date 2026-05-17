import { motion } from 'framer-motion'

const VERDICT = {
  invest_fix:      { color: 'var(--s-green)',  bg: 'rgba(18,183,106,0.08)',   border: 'rgba(18,183,106,0.25)'   },
  condition:       { color: 'var(--gold)',      bg: 'rgba(110,86,207,0.08)',   border: 'rgba(110,86,207,0.25)'   },
  fix_first:       { color: 'var(--s-amber)',  bg: 'rgba(245,165,36,0.08)',   border: 'rgba(245,165,36,0.25)'   },
  structural_pass: { color: 'var(--s-red)',    bg: 'rgba(240,68,56,0.08)',    border: 'rgba(240,68,56,0.25)'    },
}

const CARD    = { background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 20, padding: 28 }
const DIVIDER = { height: 1, background: 'var(--border)', margin: '22px 0' }
const SEC_LABEL = {
  fontSize: 10, fontWeight: 500, color: 'var(--tx-3)',
  letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 14, display: 'block',
}

function scoreColor(s) {
  if (s >= 75) return 'var(--s-green)'
  if (s >= 60) return 'var(--s-amber)'
  if (s >= 45) return 'var(--s-orange)'
  return 'var(--s-red)'
}

function PriorityAction({ action, rank }) {
  const fixColor =
    action.fix_score >= 4 ? 'var(--s-green)' :
    action.fix_score >= 3 ? 'var(--s-amber)' : 'var(--s-orange)'

  return (
    <div
      style={{
        background:   'rgba(16,19,24,0.03)',
        border:       '1px solid var(--border)',
        borderRadius: 12,
        padding:      16,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span
            style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontWeight: 700, fontSize: 13,
              color: 'var(--gold)', flexShrink: 0,
            }}
          >
            {rank}
          </span>
          <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--tx-1)' }}>{action.label}</span>
        </div>
        <span
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 11, flexShrink: 0, marginLeft: 8,
            color: fixColor,
          }}
        >
          [{action.fix_score}/5]
        </span>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, paddingLeft: 22, marginBottom: 8 }}>
        <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--gold)', fontWeight: 600 }}>
          +{action.score_impact} pts
        </span>
        {action.closing_condition ? (
          <span
            style={{
              fontSize: 11, padding: '1px 8px', borderRadius: 5,
              color: 'var(--s-red)', border: '1px solid rgba(240,68,56,0.30)',
            }}
          >
            Closing condition
          </span>
        ) : (
          <span style={{ fontSize: 11, color: 'var(--tx-3)' }}>Monitor only</span>
        )}
        {action.time_months != null && (
          <span style={{ fontSize: 11, color: 'var(--tx-3)' }}>
            ~{action.time_months}mo
          </span>
        )}
      </div>

      {action.action && (
        <p
          style={{
            fontSize: 12, color: 'var(--tx-2)', fontStyle: 'italic',
            paddingLeft: 22, lineHeight: 1.6, margin: 0,
          }}
        >
          "{action.action}"
        </p>
      )}
      {action.owner && (
        <p style={{ fontSize: 11, color: 'var(--tx-3)', paddingLeft: 22, margin: '4px 0 0' }}>
          Owner: {action.owner}
        </p>
      )}
    </div>
  )
}

export default function FixAnalysisCard({ fixData }) {
  if (!fixData) return null

  const {
    current_score, conditional_score, score_gap,
    fix_verdict, fix_verdict_label, fix_verdict_description,
    top_priority_actions, structural_problems,
  } = fixData

  const style = VERDICT[fix_verdict] || VERDICT.condition

  return (
    <motion.div
      style={CARD}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5, duration: 0.4 }}
    >
      <h2
        style={{
          fontFamily: 'Outfit, Inter, system-ui, sans-serif',
          fontSize: 22, fontWeight: 700,
          color: 'var(--tx-1)', margin: '0 0 22px', letterSpacing: '-0.01em',
        }}
      >
        Fix Analysis
      </h2>

      {/* ── Score journey ── */}
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 20,
          marginBottom: 22,
          background: 'rgba(16,19,24,0.02)',
          border: '1px solid var(--border)',
          borderRadius: 14,
          padding: '20px 24px',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: 44, fontWeight: 700,
              letterSpacing: '-0.04em', lineHeight: 1,
              color: scoreColor(current_score),
            }}
          >
            {current_score}
          </div>
          <div style={{ fontSize: 10, color: 'var(--tx-3)', marginTop: 6, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
            Current
          </div>
        </div>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
          <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 14, color: 'var(--gold)', fontWeight: 700 }}>
            +{score_gap} pts
          </span>
          <div style={{ display: 'flex', alignItems: 'center', width: '100%', gap: 8 }}>
            <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
            <span style={{ fontSize: 10, color: 'var(--tx-3)', whiteSpace: 'nowrap' }}>top 3 fixed</span>
            <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
          </div>
        </div>

        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: 44, fontWeight: 700,
              letterSpacing: '-0.04em', lineHeight: 1,
              color: scoreColor(conditional_score),
            }}
          >
            {conditional_score}
          </div>
          <div style={{ fontSize: 10, color: 'var(--tx-3)', marginTop: 6, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
            Potential
          </div>
        </div>
      </div>

      {/* ── Fix verdict ── */}
      <div
        style={{
          borderRadius: 12, padding: '14px 18px',
          background: style.bg, border: `1px solid ${style.border}`,
          marginBottom: 22,
        }}
      >
        <div
          style={{
            fontSize: 11, fontWeight: 700,
            letterSpacing: '0.07em', textTransform: 'uppercase',
            color: style.color, marginBottom: 6,
            fontFamily: 'JetBrains Mono, monospace',
          }}
        >
          {fix_verdict_label}
        </div>
        <p style={{ fontSize: 13, color: 'var(--tx-2)', lineHeight: 1.6, margin: 0 }}>
          {fix_verdict_description}
        </p>
      </div>

      {/* ── Priority actions ── */}
      {top_priority_actions?.length > 0 && (
        <div>
          <span style={SEC_LABEL}>Priority Actions</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {top_priority_actions.map((action, i) => (
              <PriorityAction key={i} action={action} rank={i + 1} />
            ))}
          </div>
        </div>
      )}

      {/* ── Structural concerns ── */}
      {structural_problems?.length > 0 && (
        <>
          <div style={DIVIDER} />
          <span style={{ ...SEC_LABEL, color: 'var(--tx-3)' }}>Structural Concerns</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {structural_problems.map((p, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 12, color: 'var(--tx-2)' }}>
                <span style={{ color: 'var(--tx-3)', flexShrink: 0, marginTop: 2 }}>·</span>
                <span>
                  {p.label}
                  {p.why_unfixable && (
                    <span style={{ color: 'var(--tx-3)', marginLeft: 5 }}>— {p.why_unfixable}</span>
                  )}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </motion.div>
  )
}
