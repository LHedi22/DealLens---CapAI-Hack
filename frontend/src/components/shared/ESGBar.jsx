const AXIS = {
  E: { label: 'Environmental', color: '#2FCC80' },
  S: { label: 'Social',        color: '#5B8AF5' },
  G: { label: 'Governance',    color: '#A78BFA' },
}

export default function ESGBar({ axis, score = 0 }) {
  const { label, color } = AXIS[axis] || { label: axis, color: 'var(--tx-2)' }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 12, color: 'var(--tx-2)', fontWeight: 500 }}>{label}</span>
        <span
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize:   13,
            fontWeight: 600,
            color,
          }}
        >
          {score}
        </span>
      </div>
      <div
        style={{
          height:       4,
          borderRadius: 2,
          background:   'rgba(0,0,0,0.08)',
          overflow:     'hidden',
        }}
      >
        <div
          style={{
            height:      '100%',
            width:       `${score}%`,
            background:  color,
            borderRadius: 2,
            transition:  'width 0.85s cubic-bezier(0.4,0,0.2,1)',
          }}
        />
      </div>
    </div>
  )
}
