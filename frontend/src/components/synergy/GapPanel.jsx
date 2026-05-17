import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import GapCard from './GapCard'
import ExternalStartupCard from './ExternalStartupCard'
import { shortlistAction, dismissGap } from '../../lib/api'

export default function GapPanel({ gaps = [], onDetect, detecting = false, onHunt }) {
  const [huntingId,   setHuntingId]   = useState(null)
  const [activeGapId, setActiveGapId] = useState(null)

  const visibleGaps = gaps.filter(g => g.status !== 'dismissed')
  const activeGap   = visibleGaps.find(g => g.id === activeGapId) ?? null

  async function handleHunt(gapId) {
    setHuntingId(gapId)
    setActiveGapId(gapId)
    try {
      await onHunt(gapId)
    } finally {
      setHuntingId(null)
    }
  }

  async function handleDismiss(gapId) {
    try {
      await dismissGap(gapId)
      if (activeGapId === gapId) setActiveGapId(null)
      onDetect && onDetect(false)
    } catch (e) {
      console.error('[GapPanel] dismiss failed', e)
    }
  }

  async function handleShortlistAction(shortlistId, action) {
    if (!activeGapId) return
    try {
      await shortlistAction(activeGapId, shortlistId, action)
    } catch (e) {
      console.error('[GapPanel] shortlist action failed', e)
    }
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, alignItems: 'start' }}>

      {/* ── Left: gap list ── */}
      <div>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14,
        }}>
          <span style={{ fontSize: 13, color: 'var(--tx-2)' }}>
            {visibleGaps.length} gap{visibleGaps.length !== 1 ? 's' : ''} detected
          </span>
          <button
            onClick={() => onDetect && onDetect(true)}
            disabled={detecting}
            style={{
              padding: '5px 14px', borderRadius: 7, fontSize: 11, fontWeight: 600,
              cursor: detecting ? 'not-allowed' : 'pointer',
              background: detecting ? 'rgba(110,86,207,0.3)' : 'rgba(110,86,207,0.1)',
              color: '#6E56CF', border: '1px solid rgba(110,86,207,0.3)',
              transition: 'all 0.15s',
            }}
          >
            {detecting ? 'Detecting…' : 'Refresh Gaps'}
          </button>
        </div>

        {visibleGaps.length === 0 ? (
          <div style={{
            border: '1px solid var(--border)', borderRadius: 12,
            padding: '40px 0', textAlign: 'center',
          }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>🔍</div>
            <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--tx-1)', marginBottom: 6 }}>
              No gaps detected yet
            </div>
            <div style={{ fontSize: 11, color: 'var(--tx-3)', marginBottom: 14 }}>
              Run gap detection to analyse portfolio needs.
            </div>
            <button
              onClick={() => onDetect && onDetect(false)}
              disabled={detecting}
              style={{
                padding: '7px 18px', borderRadius: 8, fontSize: 12, fontWeight: 600,
                cursor: detecting ? 'not-allowed' : 'pointer',
                background: '#6E56CF', color: '#fff', border: 'none',
              }}
            >
              {detecting ? 'Detecting…' : 'Detect Gaps'}
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {visibleGaps.map(gap => (
              <GapCard
                key={gap.id}
                gap={gap}
                onHunt={handleHunt}
                onDismiss={handleDismiss}
                isHunting={huntingId === gap.id}
                isActive={activeGapId === gap.id}
                onClick={() => setActiveGapId(gap.id === activeGapId ? null : gap.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* ── Right: shortlist panel ── */}
      <div>
        <AnimatePresence mode="wait">
          {activeGap && activeGap.shortlist && activeGap.shortlist.length > 0 ? (
            <motion.div
              key={`shortlist-${activeGapId}`}
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 16 }}
              transition={{ duration: 0.2 }}
            >
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14,
              }}>
                <div>
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--tx-1)' }}>
                    {activeGap.gap_label}
                  </span>
                  <span style={{ marginLeft: 8, fontSize: 10, color: 'var(--tx-3)' }}>
                    {activeGap.shortlist.length} candidate{activeGap.shortlist.length !== 1 ? 's' : ''}
                  </span>
                </div>
                <span style={{ fontSize: 9, color: 'var(--tx-3)', fontFamily: 'JetBrains Mono, monospace' }}>
                  Anthropic web search
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {activeGap.shortlist.map(company => (
                  <ExternalStartupCard
                    key={company.id}
                    company={company}
                    onAction={handleShortlistAction}
                  />
                ))}
              </div>
            </motion.div>

          ) : activeGap ? (
            <motion.div
              key={`empty-${activeGapId}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                border: '1px dashed var(--border)', borderRadius: 12,
                padding: '48px 24px', textAlign: 'center',
              }}
            >
              <div style={{ fontSize: 11, color: 'var(--tx-3)', marginBottom: 6 }}>
                No candidates yet for
              </div>
              <div style={{ fontWeight: 700, fontSize: 13, color: 'var(--tx-1)', marginBottom: 18 }}>
                {activeGap.gap_label}
              </div>
              <button
                onClick={() => handleHunt(activeGap.id)}
                disabled={huntingId === activeGap.id}
                style={{
                  padding: '7px 18px', borderRadius: 8, fontSize: 12, fontWeight: 600,
                  cursor: huntingId === activeGap.id ? 'not-allowed' : 'pointer',
                  background: huntingId === activeGap.id ? 'rgba(110,86,207,0.3)' : '#6E56CF',
                  color: '#fff', border: 'none',
                }}
              >
                {huntingId === activeGap.id ? 'Hunting…' : 'Hunt for Startups →'}
              </button>
              <div style={{ marginTop: 8, fontSize: 9, color: 'var(--tx-3)', fontFamily: 'JetBrains Mono, monospace' }}>
                Uses Anthropic web search · falls back to seed data
              </div>
            </motion.div>

          ) : (
            <motion.div
              key="placeholder"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{
                border: '1px dashed var(--border)', borderRadius: 12,
                padding: '48px 24px', textAlign: 'center',
              }}
            >
              <div style={{ fontSize: 11, color: 'var(--tx-3)', lineHeight: 1.6 }}>
                Select a gap on the left to view candidates,<br />
                or click <strong>Hunt for Startups →</strong> to find them.
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

    </div>
  )
}
