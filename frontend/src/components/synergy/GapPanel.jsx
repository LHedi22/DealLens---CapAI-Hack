import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

function urgencyColor(score) {
  if (score >= 75) return '#22c55e'
  if (score >= 60) return '#f59e0b'
  if (score >= 45) return '#f97316'
  return '#ef4444'
}

function urgencyLabel(score) {
  if (score >= 75) return 'Critical'
  if (score >= 60) return 'High'
  if (score >= 45) return 'Medium'
  return 'Low'
}

function FitScoreChip({ score }) {
  const color = urgencyColor(score)
  return (
    <span style={{
      fontFamily: 'JetBrains Mono, monospace', fontSize: 10, fontWeight: 700,
      padding: '1px 6px', borderRadius: 4,
      background: `${color}18`, color, border: `1px solid ${color}44`,
    }}>
      {score}
    </span>
  )
}

function ShortlistItem({ item }) {
  return (
    <div style={{
      padding: '10px 14px',
      border: '1px solid var(--border)',
      borderRadius: 10,
      background: 'var(--bg)',
      display: 'flex', flexDirection: 'column', gap: 4,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <span style={{ fontWeight: 700, fontSize: 13, color: 'var(--tx-1)' }}>
          {item.company_name}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <FitScoreChip score={item.fit_score} />
          {item.website && (
            <a
              href={item.website}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: 10, color: '#6E56CF', textDecoration: 'none', fontFamily: 'JetBrains Mono, monospace' }}
            >
              ↗
            </a>
          )}
        </div>
      </div>
      {item.fit_reason && (
        <p style={{ margin: 0, fontSize: 12, color: 'var(--tx-2)', lineHeight: 1.5 }}>
          {item.fit_reason}
        </p>
      )}
      {item.flags && item.flags.length > 0 && (
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 2 }}>
          {item.flags.map((f, i) => (
            <span key={i} style={{
              fontSize: 9, padding: '1px 6px', borderRadius: 4,
              background: 'rgba(239,68,68,0.08)', color: '#ef4444',
              border: '1px solid rgba(239,68,68,0.2)',
              fontFamily: 'JetBrains Mono, monospace',
            }}>
              ⚑ {f}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function GapCard({ gap, onHunt, hunting = false }) {
  const [expanded, setExpanded] = useState(false)
  const color = urgencyColor(gap.urgency_score)
  const pct   = Math.max(0, Math.min(100, gap.urgency_score))

  return (
    <div style={{
      border: '1px solid var(--border)', borderRadius: 14,
      background: 'var(--surface-1)', overflow: 'hidden',
    }}>
      {/* Card header — always visible */}
      <div
        onClick={() => setExpanded(v => !v)}
        style={{
          padding: '18px 20px', cursor: 'pointer',
          transition: 'background 0.15s',
        }}
        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(16,19,24,0.02)' }}
        onMouseLeave={e => { e.currentTarget.style.background = 'transparent' }}
      >
        {/* Top row */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, marginBottom: 10 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--tx-1)' }}>
                {gap.gap_label}
              </span>
              <span style={{
                fontSize: 9, fontWeight: 600, padding: '1px 6px', borderRadius: 4,
                background: `${color}15`, color, border: `1px solid ${color}30`,
                fontFamily: 'JetBrains Mono, monospace', textTransform: 'uppercase',
              }}>
                {urgencyLabel(gap.urgency_score)}
              </span>
            </div>
            {gap.need_description && (
              <p style={{ margin: 0, fontSize: 12, color: 'var(--tx-2)', lineHeight: 1.55 }}>
                {gap.need_description}
              </p>
            )}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2, flexShrink: 0 }}>
            <span style={{
              fontFamily: 'JetBrains Mono, monospace', fontSize: 22,
              fontWeight: 700, color, lineHeight: 1,
            }}>
              {gap.urgency_score}
            </span>
            <span style={{ fontSize: 9, color: 'var(--tx-3)', fontFamily: 'JetBrains Mono, monospace' }}>
              urgency
            </span>
          </div>
        </div>

        {/* Urgency bar */}
        <div style={{ height: 4, borderRadius: 4, background: 'rgba(16,19,24,0.06)', overflow: 'hidden', marginBottom: 12 }}>
          <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 4, transition: 'width 0.6s cubic-bezier(0.4,0,0.2,1)' }} />
        </div>

        {/* Meta row */}
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Affected companies */}
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{ fontSize: 10, color: 'var(--tx-3)', fontWeight: 500, marginRight: 2 }}>Affects:</span>
            {(gap.affected_companies || []).map(c => (
              <span key={c} style={{
                fontSize: 10, padding: '1px 7px', borderRadius: 5,
                background: 'rgba(110,86,207,0.08)', color: '#6E56CF',
                border: '1px solid rgba(110,86,207,0.2)', fontWeight: 600,
              }}>
                {c}
              </span>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 12, marginLeft: 'auto', flexWrap: 'wrap' }}>
            {gap.estimated_annual_spend && (
              <span style={{ fontSize: 11, color: 'var(--tx-2)', fontFamily: 'JetBrains Mono, monospace' }}>
                {gap.estimated_annual_spend}
              </span>
            )}
            {gap.suggested_sector && (
              <span style={{ fontSize: 10, color: 'var(--tx-3)' }}>
                Target: <strong style={{ color: 'var(--tx-2)' }}>{gap.suggested_sector}</strong>
                {gap.suggested_stage && <> · {gap.suggested_stage}</>}
              </span>
            )}
            <span style={{ fontSize: 11, color: 'var(--tx-3)' }}>
              {expanded ? '▲' : '▼'}
              {gap.shortlist?.length > 0 && (
                <span style={{ marginLeft: 5, background: 'rgba(110,86,207,0.12)', color: '#6E56CF', borderRadius: 8, padding: '0 5px', fontSize: 9 }}>
                  {gap.shortlist.length} candidates
                </span>
              )}
            </span>
          </div>
        </div>
      </div>

      {/* Shortlist — expandable */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.22 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ borderTop: '1px solid var(--border)', padding: '14px 20px 18px' }}>
              {gap.shortlist && gap.shortlist.length > 0 ? (
                <>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                    <span style={{
                      fontSize: 10, fontWeight: 500, color: 'var(--tx-3)',
                      letterSpacing: '0.08em', textTransform: 'uppercase',
                    }}>
                      Candidate Companies
                    </span>
                    <button
                      onClick={e => { e.stopPropagation(); onHunt && onHunt(gap.id) }}
                      disabled={hunting}
                      style={{
                        padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                        cursor: hunting ? 'not-allowed' : 'pointer',
                        background: 'transparent', color: 'var(--tx-3)',
                        border: '1px solid var(--border)', transition: 'all 0.15s',
                      }}
                    >
                      {hunting ? 'Hunting…' : 'Re-hunt'}
                    </button>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {gap.shortlist.map(item => (
                      <ShortlistItem key={item.id} item={item} />
                    ))}
                  </div>
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: '20px 0' }}>
                  <div style={{ fontSize: 12, color: 'var(--tx-3)', marginBottom: 10 }}>
                    No candidates shortlisted yet.
                  </div>
                  <button
                    onClick={e => { e.stopPropagation(); onHunt && onHunt(gap.id) }}
                    disabled={hunting}
                    style={{
                      padding: '6px 18px', borderRadius: 8, fontSize: 12, fontWeight: 600,
                      cursor: hunting ? 'not-allowed' : 'pointer',
                      background: hunting ? 'rgba(110,86,207,0.3)' : '#6E56CF',
                      color: '#fff', border: 'none', transition: 'background 0.15s',
                    }}
                  >
                    {hunting ? 'Hunting…' : 'Hunt Candidates →'}
                  </button>
                  <div style={{ marginTop: 6, fontSize: 10, color: 'var(--tx-3)', fontFamily: 'JetBrains Mono, monospace' }}>
                    Uses Anthropic web search · falls back to seed data
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function GapPanel({ gaps = [], onDetect, detecting = false, onHunt }) {
  const [huntingId, setHuntingId] = useState(null)

  async function handleHunt(gapId) {
    setHuntingId(gapId)
    try {
      await onHunt(gapId)
    } finally {
      setHuntingId(null)
    }
  }

  return (
    <div>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18, flexWrap: 'wrap', gap: 10 }}>
        <span style={{ fontSize: 13, color: 'var(--tx-2)' }}>
          {gaps.length} portfolio gap{gaps.length !== 1 ? 's' : ''} detected
        </span>
        <button
          onClick={() => onDetect && onDetect(true)}
          disabled={detecting}
          style={{
            padding: '6px 16px', borderRadius: 8, fontSize: 12, fontWeight: 600,
            cursor: detecting ? 'not-allowed' : 'pointer',
            background: detecting ? 'rgba(110,86,207,0.3)' : 'rgba(110,86,207,0.1)',
            color: '#6E56CF', border: '1px solid rgba(110,86,207,0.3)',
            transition: 'all 0.15s',
          }}
        >
          {detecting ? 'Detecting…' : 'Re-detect Gaps'}
        </button>
      </div>

      {gaps.length === 0 ? (
        <div style={{
          border: '1px solid var(--border)', borderRadius: 14,
          padding: '48px 0', textAlign: 'center',
        }}>
          <div style={{ fontSize: 28, marginBottom: 10 }}>🔍</div>
          <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--tx-1)', marginBottom: 6 }}>
            No gaps detected yet
          </div>
          <div style={{ fontSize: 12, color: 'var(--tx-3)', marginBottom: 16 }}>
            Run gap detection to analyse portfolio needs.
          </div>
          <button
            onClick={() => onDetect && onDetect(false)}
            disabled={detecting}
            style={{
              padding: '8px 20px', borderRadius: 8, fontSize: 13, fontWeight: 600,
              cursor: detecting ? 'not-allowed' : 'pointer',
              background: '#6E56CF', color: '#fff', border: 'none',
            }}
          >
            {detecting ? 'Detecting…' : 'Detect Gaps'}
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {gaps.map(gap => (
            <GapCard
              key={gap.id}
              gap={gap}
              onHunt={handleHunt}
              hunting={huntingId === gap.id}
            />
          ))}
        </div>
      )}
    </div>
  )
}
