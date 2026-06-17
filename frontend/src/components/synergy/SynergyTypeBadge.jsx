const TYPE_META = {
  SERVICE:  { label: 'Service Bridge',  bg: 'rgba(59,130,246,0.1)',  color: '#3b82f6', border: 'rgba(59,130,246,0.25)'  },
  CUSTOMER: { label: 'Shared Customer', bg: 'rgba(34,197,94,0.1)',   color: '#12B76A', border: 'rgba(34,197,94,0.25)'   },
  CO_DEV:   { label: 'Co-Development',  bg: 'rgba(249,115,22,0.1)',  color: '#EF6820', border: 'rgba(249,115,22,0.25)'  },
}

export default function SynergyTypeBadge({ type, small = false }) {
  const meta = TYPE_META[type] || {
    label: type, bg: 'rgba(148,163,184,0.1)', color: '#94a3b8', border: 'rgba(148,163,184,0.25)',
  }
  return (
    <span
      style={{
        display:      'inline-block',
        padding:      small ? '1px 6px' : '2px 8px',
        borderRadius: 5,
        fontSize:     small ? 9 : 10,
        fontWeight:   600,
        fontFamily:   'JetBrains Mono, monospace',
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
        background:   meta.bg,
        color:        meta.color,
        border:       `1px solid ${meta.border}`,
        whiteSpace:   'nowrap',
      }}
    >
      {meta.label}
    </span>
  )
}
