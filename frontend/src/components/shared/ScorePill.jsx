export function scoreColor(score) {
  if (score === null || score === undefined) return 'var(--tx-3)'
  if (score >= 75) return 'var(--s-green)'
  if (score >= 60) return 'var(--s-amber)'
  if (score >= 45) return 'var(--s-orange)'
  return 'var(--s-red)'
}

export function scoreBg(score) {
  if (score === null || score === undefined) return 'rgba(16,19,24,0.04)'
  if (score >= 75) return 'rgba(18,183,106,0.10)'
  if (score >= 60) return 'rgba(245,165,36,0.10)'
  if (score >= 45) return 'rgba(239,104,32,0.10)'
  return 'rgba(240,68,56,0.10)'
}

export default function ScorePill({ score }) {
  if (score === null || score === undefined) {
    return (
      <span style={{ fontFamily: 'JetBrains Mono, monospace', color: 'var(--tx-3)', fontSize: 13 }}>
        —
      </span>
    )
  }
  return (
    <span
      style={{
        fontFamily: 'JetBrains Mono, monospace',
        fontWeight: 600,
        fontSize: 13,
        color: scoreColor(score),
        letterSpacing: '-0.02em',
      }}
    >
      {score}
    </span>
  )
}
