export default function DeltaBadge({ delta }) {
  if (delta === null || delta === undefined) {
    return (
      <span style={{ fontFamily: 'JetBrains Mono, monospace', color: 'var(--tx-3)', fontSize: 13 }}>
        —
      </span>
    )
  }

  const positive = delta > 0
  const zero     = delta === 0
  const color    = zero ? 'var(--tx-3)' : positive ? 'var(--s-green)' : 'var(--s-red)'
  const sign     = positive ? '+' : ''

  return (
    <span
      style={{
        fontFamily:    'JetBrains Mono, monospace',
        fontWeight:    600,
        fontSize:      13,
        color,
        letterSpacing: '-0.02em',
      }}
    >
      {sign}{delta}
    </span>
  )
}
