import { motion } from 'framer-motion'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const FIT = {
  strong_fit:  { label: 'Strong Fit',  color: 'var(--s-green)',  bg: 'rgba(18,183,106,0.08)',  border: 'rgba(18,183,106,0.28)'  },
  neutral_fit: { label: 'Neutral Fit', color: '#5B8AF5',          bg: 'rgba(91,138,245,0.08)',  border: 'rgba(91,138,245,0.28)'  },
  weak_fit:    { label: 'Weak Fit',    color: 'var(--s-orange)', bg: 'rgba(239,104,32,0.08)',  border: 'rgba(239,104,32,0.28)'  },
  warning:     { label: 'Warning',     color: 'var(--s-red)',    bg: 'rgba(240,68,56,0.08)',   border: 'rgba(240,68,56,0.28)'   },
}

const PIE_COLORS = ['#8B7CFF','#5B8AF5','#12B76A','#6E56CF','#F5A524','#14b8a6','#ec4899','#a3e635']

const FLAGS = [
  { key: 'concentration_warning', label: 'Sector over-concentration' },
  { key: 'stage_balance_ok',      label: 'Stage imbalance',           invert: true },
  { key: 'geo_warning',           label: 'Geographic concentration' },
  { key: 'esg_degradation_flag',  label: 'ESG degradation' },
  { key: 'correlation_risk',      label: 'Correlated model risk' },
]

const CARD    = { background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 20, padding: 28 }
const DIVIDER = { height: 1, background: 'var(--border)', margin: '20px 0' }
const SEC_LABEL = {
  fontSize: 10, fontWeight: 500, color: 'var(--tx-3)',
  letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 12, display: 'block',
}

export default function PortfolioFitCard({ portfolio }) {
  if (!portfolio) return null

  const fit   = FIT[portfolio.fit_verdict] ?? FIT.neutral_fit
  const esgUp = portfolio.esg_shift >= 0

  const pieData = Object.entries(portfolio.sector_distribution || {}).map(([name, pct]) => ({
    name, value: pct,
    overweight: portfolio.overweight_sectors?.includes(name),
  }))

  return (
    <motion.div
      style={CARD}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.65, duration: 0.4 }}
    >
      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <h2
          style={{
            fontFamily: 'Outfit, Inter, system-ui, sans-serif',
            fontSize: 22, fontWeight: 700,
            color: 'var(--tx-1)', margin: 0, letterSpacing: '-0.01em',
          }}
        >
          Portfolio Fit
        </h2>
        <span
          style={{
            fontSize: 11, fontWeight: 600,
            padding: '3px 10px', borderRadius: 6,
            color: fit.color, background: fit.bg, border: `1px solid ${fit.border}`,
            fontFamily: 'JetBrains Mono, monospace',
          }}
        >
          {fit.label}
        </span>
      </div>

      {portfolio.fit_summary && (
        <p style={{ fontSize: 13, color: 'var(--tx-2)', lineHeight: 1.6, margin: '0 0 20px' }}>
          {portfolio.fit_summary}
        </p>
      )}

      {/* ── Two columns ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>

        {/* Sector pie */}
        <div>
          <span style={SEC_LABEL}>Sector Mix (after addition)</span>
          {pieData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%" cy="50%"
                    innerRadius={42} outerRadius={72}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {pieData.map((entry, i) => (
                      <Cell
                        key={entry.name}
                        fill={entry.overweight ? '#F04438' : PIE_COLORS[i % PIE_COLORS.length]}
                        opacity={0.9}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background:   '#FFFFFF',
                      border:       '1px solid var(--border)',
                      borderRadius: 10,
                      fontSize:     12,
                      color:        '#111318',
                      boxShadow:    '0 4px 16px rgba(16,24,40,0.10)',
                    }}
                    formatter={(v, n) => [`${v}%`, n]}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {pieData.map((entry, i) => (
                  <div key={entry.name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                      <div
                        style={{
                          width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                          background: entry.overweight ? '#F04438' : PIE_COLORS[i % PIE_COLORS.length],
                        }}
                      />
                      <span style={{ fontSize: 12, color: entry.overweight ? 'var(--s-red)' : 'var(--tx-2)' }}>
                        {entry.name}
                      </span>
                    </div>
                    <span
                      style={{
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: 12, fontWeight: 600,
                        color: entry.overweight ? 'var(--s-red)' : 'var(--tx-3)',
                      }}
                    >
                      {entry.value}%
                    </span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p style={{ fontSize: 12, color: 'var(--tx-3)', fontStyle: 'italic' }}>No sector data available.</p>
          )}
        </div>

        {/* Flags + ESG + correlation */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Portfolio flags */}
          <div>
            <span style={SEC_LABEL}>Flags</span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {FLAGS.map(({ key, label, invert }) => {
                const active = invert ? !portfolio[key] : !!portfolio[key]
                return (
                  <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div
                      style={{
                        width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
                        background: active ? '#F04438' : '#12B76A',
                      }}
                    />
                    <span style={{ fontSize: 12, color: active ? 'var(--s-red)' : 'var(--tx-3)' }}>
                      {label}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* ESG shift */}
          <div>
            <span style={SEC_LABEL}>ESG Portfolio Impact</span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, fontSize: 14 }}>
              {portfolio.portfolio_esg_before > 0 && (
                <>
                  <span style={{ color: 'var(--tx-3)', fontFamily: 'JetBrains Mono, monospace' }}>
                    {portfolio.portfolio_esg_before}
                  </span>
                  <span style={{ color: 'var(--tx-3)' }}>→</span>
                </>
              )}
              <span style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: 'var(--tx-1)' }}>
                {portfolio.portfolio_esg_after}
              </span>
              {portfolio.portfolio_esg_before > 0 && (
                <span
                  style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 12, fontWeight: 600,
                    color: esgUp ? 'var(--s-green)' : 'var(--s-red)',
                  }}
                >
                  ({esgUp ? '+' : ''}{portfolio.esg_shift})
                </span>
              )}
            </div>
            <p style={{ fontSize: 11, color: 'var(--tx-3)', margin: '4px 0 0' }}>
              {portfolio.portfolio_esg_before > 0 ? 'Portfolio avg ESG score' : 'First portfolio company'}
            </p>
          </div>

          {/* Correlated companies */}
          {portfolio.correlation_risk && portfolio.correlated_companies?.length > 0 && (
            <div>
              <span style={SEC_LABEL}>Correlated Companies</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {portfolio.correlated_companies.map(c => (
                  <span
                    key={c}
                    style={{
                      fontSize: 11, padding: '2px 10px', borderRadius: 6,
                      color: 'var(--s-red)',
                      background: 'rgba(240,68,56,0.08)',
                      border: '1px solid rgba(240,68,56,0.22)',
                    }}
                  >
                    {c}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Pipeline optimizer ── */}
      {portfolio.best_pair?.length >= 2 && (
        <>
          <div style={DIVIDER} />
          <span style={SEC_LABEL}>Pipeline Optimizer</span>
          <p style={{ fontSize: 12, color: 'var(--tx-2)', marginBottom: 10, lineHeight: 1.6 }}>
            {portfolio.optimizer_reason}
          </p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {portfolio.best_pair.map(name => (
              <span
                key={name}
                style={{
                  fontSize: 12, padding: '4px 12px', borderRadius: 7,
                  fontWeight: 600,
                  color: 'var(--gold)',
                  background: 'rgba(110,86,207,0.08)',
                  border: '1px solid rgba(110,86,207,0.25)',
                }}
              >
                {name}
              </span>
            ))}
          </div>
        </>
      )}
    </motion.div>
  )
}
