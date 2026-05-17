const R    = 50
const CIRC = 2 * Math.PI * R

function scoreColor(score) {
  if (score >= 75) return 'var(--s-green)'
  if (score >= 60) return 'var(--s-amber)'
  if (score >= 45) return 'var(--s-orange)'
  return 'var(--s-red)'
}

export default function ScoreGauge({ score = 0, size = 140, label = 'Final Score' }) {
  const offset = CIRC - (score / 100) * CIRC
  const color  = scoreColor(score)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
      <svg width={size} height={size} viewBox="0 0 120 120">
        {/* Track ring */}
        <circle
          cx="60" cy="60" r={R}
          fill="none"
          stroke="rgba(0,0,0,0.08)"
          strokeWidth="7"
        />
        {/* Score arc */}
        <circle
          cx="60" cy="60" r={R}
          fill="none"
          stroke={color}
          strokeWidth="7"
          strokeLinecap="round"
          strokeDasharray={CIRC}
          strokeDashoffset={offset}
          transform="rotate(-90 60 60)"
          style={{ transition: 'stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1), stroke 0.3s' }}
        />
        {/* Score number */}
        <text
          x="60" y="57"
          textAnchor="middle"
          fill={color}
          fontSize="24"
          fontWeight="700"
          fontFamily="JetBrains Mono, monospace"
          letterSpacing="-1"
        >
          {score}
        </text>
        <text x="60" y="72" textAnchor="middle" fill="var(--tx-3)" fontSize="9">
          / 100
        </text>
      </svg>
      <span
        style={{
          fontSize:      10,
          color:         'var(--tx-3)',
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          fontWeight:    500,
        }}
      >
        {label}
      </span>
    </div>
  )
}
