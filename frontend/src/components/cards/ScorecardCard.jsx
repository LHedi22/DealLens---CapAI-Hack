import ScoreGauge from '../shared/ScoreGauge'
import ConfidenceBadge from '../shared/ConfidenceBadge'
import VerdictBadge from '../shared/VerdictBadge'
import { scoreColor, scoreBg } from '../shared/ScorePill'

const DIMS = [
  { key: 'team',       label: 'Team'        },
  { key: 'market',     label: 'Market'      },
  { key: 'revenue',    label: 'Revenue'     },
  { key: 'traction',   label: 'Traction'    },
  { key: 'moat',       label: 'Moat'        },
  { key: 'scalability',label: 'Scalability' },
]

const CARD = {
  background:   'var(--surface-1)',
  border:       '1px solid var(--border)',
  borderRadius: 20,
  padding:      28,
  boxShadow:    '0 1px 3px rgba(16,24,40,0.06)',
}

const DIVIDER = { height: 1, background: 'var(--border)', margin: '22px 0' }

const SEC_LABEL = {
  fontSize:      10,
  fontWeight:    500,
  color:         'var(--tx-3)',
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
  marginBottom:  12,
  display:       'block',
}

export default function ScorecardCard({ data }) {
  const {
    startup_name, sector, stage,
    final_score, business_score, adjusted_business, esg_composite, conviction_delta,
    confidence_level, data_completeness,
    verdict, verdict_reason,
    dimension_scores = {}, top_strengths = [], top_risks = [],
  } = data

  const deltaSign  = conviction_delta > 0 ? '+' : ''
  const deltaColor =
    conviction_delta > 0 ? 'var(--s-green)' :
    conviction_delta < 0 ? 'var(--s-red)'   : 'var(--tx-3)'

  const adj = adjusted_business ?? (business_score + (conviction_delta || 0))

  return (
    <div style={CARD}>

      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
        <div>
          <h2
            style={{
              fontFamily:    "'Outfit', 'Inter', system-ui, sans-serif",
              fontSize:      28,
              fontWeight:    700,
              color:         'var(--tx-1)',
              margin:        0,
              letterSpacing: '-0.02em',
              lineHeight:    1.1,
            }}
          >
            {startup_name}
          </h2>
          <p style={{ fontSize: 13, color: 'var(--tx-2)', margin: '6px 0 0 0' }}>
            {sector} · {stage}
          </p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8 }}>
          <VerdictBadge decision={verdict} />
          <ConfidenceBadge level={confidence_level} completeness={data_completeness} />
        </div>
      </div>

      <div style={DIVIDER} />

      {/* ── Score row ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
        <ScoreGauge score={final_score} label="Final Score" size={130} />

        <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10 }}>
          {[
            { label: 'Business', value: business_score },
            { label: 'ESG',      value: esg_composite  },
            {
              label: 'Memory Δ',
              value: conviction_delta ?? 0,
              isRaw: true,
              rawColor: deltaColor,
              rawSign: deltaSign,
            },
          ].map(({ label, value, isRaw, rawColor, rawSign }) => (
            <div
              key={label}
              style={{
                background:   isRaw ? 'rgba(16,19,24,0.03)' : scoreBg(value),
                border:       '1px solid var(--border)',
                borderRadius: 12,
                padding:      '14px 12px',
                textAlign:    'center',
              }}
            >
              <div style={{ fontSize: 10, color: 'var(--tx-3)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 6 }}>
                {label}
              </div>
              <div
                style={{
                  fontFamily:    'JetBrains Mono, monospace',
                  fontSize:      24,
                  fontWeight:    700,
                  letterSpacing: '-0.03em',
                  color:         isRaw ? rawColor : scoreColor(value),
                }}
              >
                {isRaw ? `${rawSign}${value}` : value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Score formula ── */}
      {conviction_delta !== 0 && conviction_delta != null && (
        <>
          <div style={DIVIDER} />
          <div
            style={{
              background:   'rgba(16,19,24,0.03)',
              border:       '1px solid var(--border)',
              borderRadius: 10,
              padding:      '12px 16px',
              fontFamily:   'JetBrains Mono, monospace',
              fontSize:     12,
              color:        'var(--tx-3)',
              lineHeight:   1.8,
            }}
          >
            <div>
              Business {business_score}
              {' '}<span style={{ color: deltaColor }}>{deltaSign}{conviction_delta}</span>
              {' '}(memory) = <span style={{ color: 'var(--tx-1)' }}>{adj}</span> adjusted
            </div>
            <div>
              Final = ({adj} × 0.70) + ({esg_composite} × 0.30) ={' '}
              <span style={{ color: scoreColor(final_score), fontWeight: 700 }}>{final_score}</span>
            </div>
          </div>
        </>
      )}

      {/* ── Verdict reason ── */}
      {verdict_reason && (
        <>
          <div style={DIVIDER} />
          <div
            style={{
              borderLeft:  '2px solid var(--gold)',
              paddingLeft: 14,
              fontSize:    13,
              color:       'var(--tx-2)',
              fontStyle:   'italic',
              lineHeight:  1.6,
            }}
          >
            {verdict_reason}
          </div>
        </>
      )}

      <div style={DIVIDER} />

      {/* ── Dimension scores ── */}
      <span style={SEC_LABEL}>Dimension Scores</span>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8 }}>
        {DIMS.map(({ key, label }) => {
          const val = dimension_scores[key] ?? 0
          return (
            <div
              key={key}
              style={{
                background:     scoreBg(val),
                borderRadius:   10,
                padding:        '10px 12px',
                display:        'flex',
                justifyContent: 'space-between',
                alignItems:     'center',
              }}
            >
              <span style={{ fontSize: 11, color: 'var(--tx-2)' }}>{label}</span>
              <span
                style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize:   15,
                  fontWeight: 700,
                  color:      scoreColor(val),
                }}
              >
                {val}
              </span>
            </div>
          )
        })}
      </div>

      <div style={DIVIDER} />

      {/* ── Strengths + Risks ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <div>
          <span style={{ ...SEC_LABEL, color: 'var(--s-green)' }}>Top Strengths</span>
          <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {top_strengths.map((s, i) => (
              <li key={i} style={{ display: 'flex', gap: 10, fontSize: 12, color: 'var(--tx-2)', lineHeight: 1.5 }}>
                <span style={{ color: 'var(--s-green)', flexShrink: 0, marginTop: 1, fontWeight: 600 }}>✓</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <span style={{ ...SEC_LABEL, color: 'var(--s-red)' }}>Top Risks</span>
          <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {top_risks.map((r, i) => (
              <li key={i} style={{ display: 'flex', gap: 10, fontSize: 12, color: 'var(--tx-2)', lineHeight: 1.5 }}>
                <span style={{ color: 'var(--s-red)', flexShrink: 0, marginTop: 1, fontWeight: 700 }}>!</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

    </div>
  )
}
