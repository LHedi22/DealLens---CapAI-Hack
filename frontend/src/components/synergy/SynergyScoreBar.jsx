function scoreColor(score) {
  if (score >= 75) return '#22c55e'
  if (score >= 60) return '#f59e0b'
  if (score >= 45) return '#f97316'
  return '#ef4444'
}

export default function SynergyScoreBar({ score, label, showNumber = true, height = 6 }) {
  const pct   = Math.max(0, Math.min(100, score || 0))
  const color = scoreColor(pct)

  return (
    <div style={{ width: '100%' }}>
      {(label || showNumber) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
          {label && (
            <span style={{ fontSize: 11, color: 'var(--tx-3)', fontWeight: 500 }}>{label}</span>
          )}
          {showNumber && (
            <span style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: 11, fontWeight: 700,
              color,
            }}>
              {pct}
            </span>
          )}
        </div>
      )}
      <div
        style={{
          width: '100%', height, borderRadius: height,
          background: 'rgba(16,19,24,0.06)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${pct}%`, height: '100%',
            background: color,
            borderRadius: height,
            transition: 'width 0.6s cubic-bezier(0.4,0,0.2,1)',
          }}
        />
      </div>
    </div>
  )
}
