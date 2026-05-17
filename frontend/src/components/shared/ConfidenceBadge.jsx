const LEVELS = {
  HIGH:   { color: 'var(--s-green)',  dot: '#2FCC80' },
  MEDIUM: { color: 'var(--s-amber)',  dot: '#F5A623' },
  LOW:    { color: 'var(--s-red)',    dot: '#E84545' },
}

export default function ConfidenceBadge({ level, completeness }) {
  if (!level) return null
  const l = LEVELS[level.toUpperCase()] || { color: 'var(--tx-2)', dot: 'var(--tx-3)' }

  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <span
        style={{
          width: 6, height: 6,
          borderRadius: '50%',
          background: l.dot,
          flexShrink: 0,
        }}
      />
      <span
        style={{
          fontSize:      11,
          fontWeight:    500,
          color:         l.color,
          fontFamily:    'JetBrains Mono, monospace',
          letterSpacing: '0.04em',
        }}
      >
        {level.toUpperCase()}
        {completeness != null && (
          <span style={{ color: 'var(--tx-3)', fontWeight: 400, marginLeft: 5 }}>
            {completeness}%
          </span>
        )}
      </span>
    </span>
  )
}
