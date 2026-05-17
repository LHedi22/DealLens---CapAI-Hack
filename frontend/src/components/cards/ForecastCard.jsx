import { motion } from 'framer-motion'

const DISCLAIMER = 'AI-reasoned estimates. Not a financial model. Use for directional comparison only.'

const CARD    = { background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 20, padding: 28 }
const DIVIDER = { height: 1, background: 'var(--border)', margin: '22px 0' }
const SEC_LABEL = {
  fontSize: 10, fontWeight: 500, color: 'var(--tx-3)',
  letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 14, display: 'block',
}

function fmt(n)  { return n != null ? `$${n.toLocaleString()}` : '—' }
function pct(n)  { return n != null ? `${n > 0 ? '+' : ''}${n}%` : '—' }

function RevenueSection({ rt }) {
  const maxVal = Math.max(rt.base_case_12m || 0, rt.optimistic_12m || 0, rt.conservative_12m || 0)
  const barW   = val => maxVal > 0 && val ? Math.round((val / maxVal) * 100) : 0

  const scenarios = [
    { label: 'Base case',    val: rt.base_case_12m,    pctV: rt.base_case_growth_pct,    color: 'var(--gold)'     },
    { label: 'Optimistic',   val: rt.optimistic_12m,   pctV: rt.optimistic_growth_pct,   color: 'var(--s-green)'  },
    { label: 'Conservative', val: rt.conservative_12m, pctV: rt.conservative_growth_pct, color: 'var(--tx-2)'     },
  ]

  return (
    <div>
      <span style={SEC_LABEL}>Revenue Trajectory (12 months)</span>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18 }}>
        <span style={{ fontSize: 12, color: 'var(--tx-3)', width: 110 }}>Current</span>
        <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: 'var(--tx-2)' }}>
          {fmt(rt.base_case_current)}
        </span>
      </div>

      {scenarios.map(({ label, val, pctV, color }) => (
        <div key={label} style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
            <span style={{ fontSize: 12, color: 'var(--tx-3)', width: 110 }}>{label}</span>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, fontWeight: 600, color }}>{fmt(val)}</span>
            <span style={{ fontSize: 11, color: 'var(--tx-3)', fontFamily: 'JetBrains Mono, monospace' }}>{pct(pctV)}</span>
          </div>
          <div style={{ height: 4, background: 'rgba(0,0,0,0.08)', borderRadius: 2, overflow: 'hidden' }}>
            <motion.div
              style={{ height: '100%', background: color, borderRadius: 2 }}
              initial={{ width: 0 }}
              animate={{ width: `${barW(val)}%` }}
              transition={{ duration: 0.8, delay: 0.4 }}
            />
          </div>
        </div>
      ))}

      {rt.key_assumption && (
        <p style={{ fontSize: 11, color: 'var(--tx-3)', fontStyle: 'italic', margin: 0 }}>
          {rt.key_assumption}
        </p>
      )}
    </div>
  )
}

function ProbabilitySection({ sp }) {
  const prob      = sp.probability_pct || 0
  const base      = sp.sector_base_rate_pct || 0
  const probColor =
    prob >= 60 ? 'var(--s-green)' :
    prob >= 40 ? 'var(--s-amber)' : 'var(--s-red)'

  return (
    <div>
      <span style={SEC_LABEL}>
        Probability of Reaching {sp.milestone || 'Next Milestone'}
        {sp.horizon_months ? ` (${sp.horizon_months}m)` : ''}
      </span>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 16 }}>
        <span
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 48, fontWeight: 700,
            letterSpacing: '-0.04em', lineHeight: 1,
            color: probColor,
          }}
        >
          {prob}%
        </span>
        <div style={{ fontSize: 12, color: 'var(--tx-3)', lineHeight: 1.8 }}>
          <div>Sector base rate: <span style={{ fontFamily: 'JetBrains Mono, monospace', color: 'var(--tx-2)' }}>{base}%</span></div>
          <div>Confidence: <span style={{ color: 'var(--tx-2)' }}>{sp.confidence}</span></div>
        </div>
      </div>

      <div style={{ height: 5, background: 'rgba(0,0,0,0.08)', borderRadius: 3, overflow: 'hidden', marginBottom: 14 }}>
        <motion.div
          style={{ height: '100%', background: probColor, borderRadius: 3 }}
          initial={{ width: 0 }}
          animate={{ width: `${prob}%` }}
          transition={{ duration: 0.8, delay: 0.5 }}
        />
      </div>

      {sp.adjustments?.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          {sp.adjustments.map((adj, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12 }}>
              <span
                style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  width: 36,
                  textAlign: 'right',
                  flexShrink: 0,
                  color: adj.value_pct >= 0 ? 'var(--s-green)' : 'var(--s-red)',
                  fontWeight: 600,
                }}
              >
                {adj.value_pct >= 0 ? '+' : ''}{adj.value_pct}%
              </span>
              <span style={{ color: 'var(--tx-2)' }}>{adj.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ROISection({ roi }) {
  const confColor = { HIGH: 'var(--s-green)', MEDIUM: 'var(--s-amber)', LOW: 'var(--tx-2)' }[roi.confidence] || 'var(--tx-2)'

  return (
    <div>
      <span style={SEC_LABEL}>Expected ROI ({roi.horizon_years || 5}-year)</span>

      {roi.probability_weighted_multiple ? (
        <>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 14, marginBottom: 10 }}>
            <span
              style={{
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: 36, fontWeight: 700,
                color: 'var(--gold)', letterSpacing: '-0.03em', lineHeight: 1,
              }}
            >
              {roi.probability_weighted_multiple}×
            </span>
            <span style={{ fontSize: 12, color: 'var(--tx-3)' }}>probability-weighted</span>
            <span
              style={{
                fontSize: 10, fontWeight: 600,
                padding: '2px 7px', borderRadius: 5,
                color: confColor, border: `1px solid ${confColor}`,
                fontFamily: 'JetBrains Mono, monospace',
              }}
            >
              {roi.confidence}
            </span>
          </div>

          {roi.expected_multiple && (
            <p style={{ fontSize: 12, color: 'var(--tx-3)', margin: '0 0 8px' }}>
              Success-scenario:{' '}
              <span style={{ fontFamily: 'JetBrains Mono, monospace', color: 'var(--tx-2)' }}>
                {roi.expected_multiple}×
              </span>
            </p>
          )}

          {roi.comparables_used?.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {roi.comparables_used.map((c, i) => (
                <p key={i} style={{ fontSize: 11, color: 'var(--tx-3)', margin: 0 }}>· {c}</p>
              ))}
            </div>
          )}
        </>
      ) : (
        <p style={{ fontSize: 13, color: 'var(--tx-3)', fontStyle: 'italic', margin: 0 }}>
          {roi.note || 'No comparable exits in fund memory yet.'}
        </p>
      )}
    </div>
  )
}

function SectorTrendSection({ st }) {
  const signalColor = { POSITIVE: 'var(--s-green)', NEUTRAL: 'var(--tx-3)', CAUTIOUS: 'var(--s-orange)' }[st.signal] || 'var(--tx-3)'
  const trendIcon   = st.trend_direction === 'improving' ? '↑' : st.trend_direction === 'declining' ? '↓' : '→'

  return (
    <div>
      <span style={SEC_LABEL}>Sector Trend — {st.sector}</span>
      <div style={{ display: 'flex', gap: 24, marginBottom: 8, fontSize: 13 }}>
        <span style={{ color: 'var(--tx-2)' }}>
          Fund win rate:{' '}
          <span style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700 }}>{st.fund_win_rate_pct}%</span>
        </span>
        <span style={{ color: signalColor, fontWeight: 600 }}>
          {trendIcon} {st.trend_direction} · {st.signal}
        </span>
      </div>
      {st.startup_growth_claim && (
        <p style={{ fontSize: 12, color: 'var(--tx-3)', margin: '0 0 4px' }}>
          Startup claims:{' '}
          <span style={{ color: 'var(--tx-2)' }}>{st.startup_growth_claim} market growth</span>
        </p>
      )}
      {st.note && <p style={{ fontSize: 12, color: 'var(--tx-3)', margin: 0 }}>{st.note}</p>}
    </div>
  )
}

export default function ForecastCard({ forecast }) {
  if (!forecast) return null
  const { revenue_trajectory, success_probability, roi_estimate, sector_trend } = forecast

  return (
    <motion.div
      style={CARD}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.35, duration: 0.4 }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <h2
          style={{
            fontFamily: 'Outfit, Inter, system-ui, sans-serif',
            fontSize: 22, fontWeight: 700,
            color: 'var(--tx-1)', margin: 0, letterSpacing: '-0.01em',
          }}
        >
          Forecast
        </h2>
        <span style={{ fontSize: 11, color: 'var(--tx-3)' }}>12m revenue · 24m probability · 5yr ROI</span>
      </div>

      {/* Disclaimer */}
      <div
        style={{
          background:    'rgba(110,86,207,0.06)',
          border:        '1px solid rgba(110,86,207,0.20)',
          borderRadius:  10,
          padding:       '10px 14px',
          marginBottom:  24,
          fontSize:      11,
          color:         'var(--gold)',
          lineHeight:    1.5,
        }}
      >
        ⚠ {DISCLAIMER}
      </div>

      {revenue_trajectory && <RevenueSection rt={revenue_trajectory} />}
      {success_probability && <><div style={DIVIDER} /><ProbabilitySection sp={success_probability} /></>}
      {roi_estimate        && <><div style={DIVIDER} /><ROISection roi={roi_estimate} /></>}
      {sector_trend        && <><div style={DIVIDER} /><SectorTrendSection st={sector_trend} /></>}
    </motion.div>
  )
}
