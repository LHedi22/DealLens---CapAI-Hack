import { motion } from 'framer-motion'

const CARD = { background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 20, padding: 28 }

export default function BlindSpotCard({ blindSpots }) {
  if (!blindSpots?.length) return null

  return (
    <motion.div
      style={CARD}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.8, duration: 0.4 }}
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
          Blind Spot Report
        </h2>
        <span
          style={{
            fontSize: 11, padding: '3px 10px', borderRadius: 12,
            background: 'rgba(110,86,207,0.08)',
            border: '1px solid rgba(110,86,207,0.22)',
            color: 'var(--gold)',
            fontFamily: 'JetBrains Mono, monospace',
          }}
        >
          {blindSpots.length} gap{blindSpots.length !== 1 ? 's' : ''} detected
        </span>
      </div>

      <p style={{ fontSize: 12, color: 'var(--tx-3)', lineHeight: 1.6, margin: '0 0 20px' }}>
        Missing information that could materially change the investment thesis. Raise these before committing.
      </p>

      {/* ── Blind spot cards ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {blindSpots.map((spot, i) => (
          <div
            key={i}
            style={{
              background:   'rgba(16,19,24,0.03)',
              border:       '1px solid var(--border)',
              borderRadius: 14,
              padding:      18,
            }}
          >
            {/* Number + field */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
              <span
                style={{
                  width: 24, height: 24, borderRadius: '50%',
                  background: 'rgba(110,86,207,0.10)',
                  border: '1px solid rgba(110,86,207,0.25)',
                  color: 'var(--gold)',
                  fontSize: 11, fontWeight: 700,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                  fontFamily: 'JetBrains Mono, monospace',
                }}
              >
                {i + 1}
              </span>
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--tx-1)', textTransform: 'capitalize' }}>
                {spot.field?.replace(/_/g, ' ')}
              </span>
            </div>

            {/* Risk */}
            <p style={{ fontSize: 12, color: 'var(--tx-2)', lineHeight: 1.6, margin: '0 0 12px', paddingLeft: 36 }}>
              {spot.risk}
            </p>

            {/* Question */}
            <div
              style={{
                marginLeft: 36,
                background: 'rgba(16,19,24,0.03)',
                border: '1px solid var(--border)',
                borderRadius: 10,
                padding: '10px 14px',
                display: 'flex', alignItems: 'flex-start', gap: 10,
              }}
            >
              <span
                style={{
                  fontSize: 11, fontWeight: 700,
                  color: 'var(--gold)', flexShrink: 0,
                  marginTop: 1, letterSpacing: '0.04em',
                  fontFamily: 'JetBrains Mono, monospace',
                }}
              >
                ASK
              </span>
              <p style={{ fontSize: 12, color: 'var(--tx-2)', fontStyle: 'italic', lineHeight: 1.6, margin: 0 }}>
                "{spot.question}"
              </p>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  )
}
