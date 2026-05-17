const VERDICT = {
  pursue:    { label: 'PURSUE',    color: 'var(--s-green)',  bg: 'rgba(47,204,128,0.08)',  border: 'rgba(47,204,128,0.28)'  },
  watch:     { label: 'WATCH',     color: 'var(--s-amber)',  bg: 'rgba(245,166,35,0.08)',  border: 'rgba(245,166,35,0.28)'  },
  soft_pass: { label: 'SOFT PASS', color: 'var(--s-orange)', bg: 'rgba(240,112,40,0.08)',  border: 'rgba(240,112,40,0.28)'  },
  pass:      { label: 'PASS',      color: 'var(--s-red)',    bg: 'rgba(232,69,69,0.08)',   border: 'rgba(232,69,69,0.28)'   },
}

export default function VerdictBadge({ decision }) {
  if (!decision) return <span style={{ color: 'var(--tx-3)', fontSize: 12 }}>—</span>
  const key = decision.toLowerCase()
  const v = VERDICT[key] || {
    label:  decision.toUpperCase(),
    color:  'var(--tx-2)',
    bg:     'rgba(16,19,24,0.05)',
    border: 'rgba(16,19,24,0.12)',
  }
  return (
    <span
      style={{
        display:        'inline-flex',
        alignItems:     'center',
        padding:        '3px 9px',
        borderRadius:   6,
        fontSize:       11,
        fontWeight:     600,
        letterSpacing:  '0.06em',
        fontFamily:     'JetBrains Mono, monospace',
        color:          v.color,
        background:     v.bg,
        border:         `1px solid ${v.border}`,
        whiteSpace:     'nowrap',
      }}
    >
      {v.label}
    </span>
  )
}
