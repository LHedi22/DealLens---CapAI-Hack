import ESGBar from '../shared/ESGBar'

const TIER = {
  'Strong':        { color: 'var(--s-green)',  bg: 'rgba(47,204,128,0.08)',  border: 'rgba(47,204,128,0.28)'  },
  'Adequate':      { color: '#5B8AF5',          bg: 'rgba(91,138,245,0.08)',  border: 'rgba(91,138,245,0.28)'  },
  'Weak':          { color: 'var(--s-orange)', bg: 'rgba(240,112,40,0.08)',  border: 'rgba(240,112,40,0.28)'  },
  'Critical Risk': { color: 'var(--s-red)',    bg: 'rgba(232,69,69,0.08)',   border: 'rgba(232,69,69,0.28)'   },
}

const VERIF_COLOR = {
  High:   'var(--s-green)',
  Medium: 'var(--s-amber)',
  Low:    'var(--s-red)',
}

const CARD    = { background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 20, padding: 28 }
const DIVIDER = { height: 1, background: 'var(--border)', margin: '20px 0' }
const SEC_LABEL = {
  fontSize: 10, fontWeight: 500, color: 'var(--tx-3)',
  letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 12, display: 'block',
}

export default function ESGCard({ data }) {
  const {
    esg_composite, esg_e, esg_s, esg_g,
    esg_tier, esg_verifiability, esg_reasoning,
    red_flags_triggered = [], red_flag_details = [], most_critical_esg_flag,
  } = data

  const tier  = TIER[esg_tier] || TIER['Adequate']
  const vColor = VERIF_COLOR[esg_verifiability] || 'var(--tx-2)'

  return (
    <div style={CARD}>

      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2
          style={{
            fontFamily: 'Outfit, Inter, system-ui, sans-serif',
            fontSize: 22, fontWeight: 700,
            color: 'var(--tx-1)', margin: 0, letterSpacing: '-0.01em',
          }}
        >
          ESG Analysis
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span
            style={{
              fontSize: 11, fontWeight: 600,
              padding: '3px 10px', borderRadius: 6,
              color: tier.color, background: tier.bg, border: `1px solid ${tier.border}`,
              fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.04em',
            }}
          >
            {esg_tier}
          </span>
          <span style={{ fontSize: 11, color: 'var(--tx-3)' }}>
            Verifiability:{' '}
            <span style={{ color: vColor, fontWeight: 600 }}>{esg_verifiability}</span>
          </span>
        </div>
      </div>

      {/* ── Composite score ── */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, margin: '18px 0 20px' }}>
        <span
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 44, fontWeight: 700,
            color: 'var(--tx-1)', letterSpacing: '-0.04em', lineHeight: 1,
          }}
        >
          {esg_composite}
        </span>
        <span style={{ fontSize: 14, color: 'var(--tx-3)' }}>/ 100 composite</span>
      </div>

      {/* ── E / S / G bars ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <ESGBar axis="E" score={esg_e} />
        <ESGBar axis="S" score={esg_s} />
        <ESGBar axis="G" score={esg_g} />
      </div>

      <div style={DIVIDER} />

      {/* ── Red flags ── */}
      {red_flags_triggered.length > 0 ? (
        <div>
          <span style={SEC_LABEL}>
            Red Flags Triggered ({red_flags_triggered.length})
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {red_flag_details.length > 0
              ? red_flag_details.map((detail, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex', alignItems: 'flex-start', gap: 10,
                      fontSize: 12,
                      background: 'rgba(232,69,69,0.06)',
                      border: '1px solid rgba(232,69,69,0.18)',
                      borderRadius: 10, padding: '10px 14px',
                    }}
                  >
                    <span
                      style={{
                        fontFamily: 'JetBrains Mono, monospace',
                        fontWeight: 700, color: 'var(--s-red)',
                        flexShrink: 0, fontSize: 11,
                      }}
                    >
                      {detail.code}
                    </span>
                    <span style={{ color: 'var(--tx-2)', flex: 1, lineHeight: 1.5 }}>{detail.description}</span>
                    <span
                      style={{
                        fontFamily: 'JetBrains Mono, monospace',
                        color: 'var(--s-red)', flexShrink: 0, fontWeight: 600, fontSize: 11,
                      }}
                    >
                      −{detail.deduction}
                    </span>
                  </div>
                ))
              : red_flags_triggered.map((code, i) => (
                  <div
                    key={i}
                    style={{
                      fontSize: 12, color: 'var(--s-red)',
                      background: 'rgba(232,69,69,0.06)',
                      border: '1px solid rgba(232,69,69,0.18)',
                      borderRadius: 10, padding: '10px 14px',
                      fontFamily: 'JetBrains Mono, monospace',
                    }}
                  >
                    {code}
                  </div>
                ))
            }
          </div>
          {most_critical_esg_flag && (
            <p style={{ fontSize: 11, color: 'var(--tx-3)', marginTop: 10 }}>
              Most critical:{' '}
              <span style={{ color: 'var(--s-red)', fontFamily: 'JetBrains Mono, monospace' }}>
                {most_critical_esg_flag}
              </span>
            </p>
          )}
        </div>
      ) : (
        <div
          style={{
            display: 'flex', alignItems: 'center', gap: 10,
            fontSize: 12, color: 'var(--s-green)',
            background: 'rgba(47,204,128,0.06)',
            border: '1px solid rgba(47,204,128,0.18)',
            borderRadius: 10, padding: '10px 14px',
          }}
        >
          <span style={{ fontWeight: 700 }}>✓</span>
          <span>No ESG red flags triggered</span>
        </div>
      )}

      {/* ── Reasoning ── */}
      {esg_reasoning && (
        <>
          <div style={DIVIDER} />
          <span style={SEC_LABEL}>ESG Reasoning</span>
          <p style={{ fontSize: 12, color: 'var(--tx-2)', lineHeight: 1.7, margin: 0 }}>{esg_reasoning}</p>
        </>
      )}
    </div>
  )
}
