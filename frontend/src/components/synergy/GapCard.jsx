function urgencyColor(score) {
  if (score >= 75) return '#F04438'
  if (score >= 50) return '#F5A524'
  return '#12B76A'
}

function urgencyLabel(score) {
  if (score >= 75) return 'Critical'
  if (score >= 50) return 'High'
  return 'Moderate'
}

function StatusBadge({ status }) {
  const config = {
    open:     { color: 'var(--tx-3)',  bg: 'rgba(148,163,184,0.1)', label: 'Open' },
    hunting:  { color: '#6E56CF',      bg: 'rgba(110,86,207,0.1)', label: 'Candidates Found' },
    filled:   { color: '#12B76A',      bg: 'rgba(34,197,94,0.1)',  label: 'Filled' },
  }
  const c = config[status] || config.open
  return (
    <span style={{
      fontSize: 9, fontWeight: 600, padding: '2px 7px', borderRadius: 4,
      background: c.bg, color: c.color, fontFamily: 'JetBrains Mono, monospace',
      textTransform: 'uppercase', letterSpacing: '0.06em',
    }}>
      {c.label}
    </span>
  )
}

export default function GapCard({ gap, onHunt, onDismiss, isHunting, isActive, onClick }) {
  const color = urgencyColor(gap.urgency_score)
  const pct   = Math.max(0, Math.min(100, gap.urgency_score))

  return (
    <div
      onClick={onClick}
      style={{
        border: `1px solid ${isActive ? '#6E56CF' : 'var(--border)'}`,
        borderRadius: 12,
        background: isActive ? 'rgba(110,86,207,0.05)' : 'var(--surface-1)',
        padding: '14px 16px',
        cursor: 'pointer',
        transition: 'all 0.15s',
      }}
    >
      {/* Top row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
            <span style={{ fontWeight: 700, fontSize: 13, color: 'var(--tx-1)' }}>
              {gap.gap_label}
            </span>
            <StatusBadge status={gap.status} />
          </div>
          {gap.need_description && (
            <p style={{ margin: 0, fontSize: 11, color: 'var(--tx-3)', lineHeight: 1.4 }}>
              {gap.need_description}
            </p>
          )}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', flexShrink: 0 }}>
          <span style={{
            fontFamily: 'JetBrains Mono, monospace', fontSize: 20,
            fontWeight: 700, color, lineHeight: 1,
          }}>
            {gap.urgency_score}
          </span>
          <span style={{ fontSize: 9, color: 'var(--tx-3)', fontFamily: 'JetBrains Mono, monospace' }}>
            {urgencyLabel(gap.urgency_score)}
          </span>
        </div>
      </div>

      {/* Urgency bar */}
      <div style={{ height: 3, borderRadius: 3, background: 'rgba(16,19,24,0.06)', overflow: 'hidden', marginBottom: 10 }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 3, transition: 'width 0.5s ease' }} />
      </div>

      {/* Affected companies + sector tag */}
      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center', marginBottom: 10 }}>
        {(gap.affected_companies || []).map(c => (
          <span key={c} style={{
            fontSize: 9, padding: '1px 6px', borderRadius: 4,
            background: 'rgba(110,86,207,0.08)', color: '#6E56CF',
            border: '1px solid rgba(110,86,207,0.2)', fontWeight: 600,
          }}>
            {c}
          </span>
        ))}
        {gap.suggested_sector && (
          <span style={{
            fontSize: 9, padding: '1px 6px', borderRadius: 4,
            background: 'rgba(148,163,184,0.1)', color: 'var(--tx-3)',
            marginLeft: 'auto',
          }}>
            {gap.suggested_sector}{gap.suggested_stage ? ` · ${gap.suggested_stage}` : ''}
          </span>
        )}
      </div>

      {/* Simulated results notice */}
      {gap.shortlist?.some(s => s.flags?.some(f => f.includes('Simulated'))) && (
        <div style={{
          fontSize: 10, color: '#F5A524', background: 'rgba(245,158,11,0.08)',
          border: '1px solid rgba(245,158,11,0.25)', borderRadius: 6,
          padding: '4px 8px', marginBottom: 8,
        }}>
          Simulated results — connect Anthropic API for live search
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 6 }} onClick={e => e.stopPropagation()}>
        <button
          onClick={() => onHunt && onHunt(gap.id)}
          disabled={isHunting}
          style={{
            flex: 1, padding: '5px 10px', borderRadius: 7, fontSize: 11, fontWeight: 600,
            cursor: isHunting ? 'not-allowed' : 'pointer',
            background: isHunting ? 'rgba(110,86,207,0.3)' : '#6E56CF',
            color: '#fff', border: 'none', transition: 'background 0.15s',
          }}
        >
          {isHunting
            ? '⏳ Hunting…'
            : gap.status === 'hunting'
              ? '↺ Re-hunt'
              : 'Hunt for Startups →'
          }
        </button>
        <button
          onClick={() => onDismiss && onDismiss(gap.id)}
          style={{
            padding: '5px 10px', borderRadius: 7, fontSize: 11, fontWeight: 600,
            cursor: 'pointer', background: 'transparent',
            color: 'var(--tx-3)', border: '1px solid var(--border)',
            transition: 'all 0.15s',
          }}
        >
          Dismiss
        </button>
      </div>
    </div>
  )
}
