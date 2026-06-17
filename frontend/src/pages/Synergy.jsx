import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import PortfolioGraph from '../components/synergy/PortfolioGraph'
import SynergyPairTable from '../components/synergy/SynergyPairTable'
import GapPanel from '../components/synergy/GapPanel'
import {
  getSynergyStatus, runSynergy,
  getSynergyPairs, getSynergyGraph, decideSynergyPair,
  getSynergyGaps, detectSynergyGaps, huntSynergyGap,
} from '../lib/api'

const TAB_STYLE = (active) => ({
  padding: '7px 18px', borderRadius: 8, fontSize: 13, fontWeight: 600,
  cursor: 'pointer', border: '1px solid',
  borderColor:  active ? '#6E56CF' : 'var(--border)',
  background:   active ? 'rgba(110,86,207,0.1)' : 'transparent',
  color:        active ? '#6E56CF' : 'var(--tx-2)',
  transition:   'all 0.15s',
})

const STAT = ({ label, value, color }) => (
  <div style={{
    background: 'var(--surface-1)', border: '1px solid var(--border)',
    borderRadius: 12, padding: '14px 20px', minWidth: 110,
  }}>
    <div style={{ fontSize: 10, color: 'var(--tx-3)', fontWeight: 500, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 6 }}>{label}</div>
    <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 24, fontWeight: 700, color: color || 'var(--tx-1)' }}>{value ?? '—'}</div>
  </div>
)

export default function Synergy() {
  const [tab,            setTab]            = useState('pairs')
  const [status,         setStatus]         = useState(null)
  const [pairs,          setPairs]          = useState([])
  const [graphData,      setGraphData]      = useState({ nodes: [], edges: [] })
  const [gaps,           setGaps]           = useState([])
  const [selectedPairId, setSelectedPairId] = useState(null)
  const [running,        setRunning]        = useState(false)
  const [detecting,      setDetecting]      = useState(false)
  const [error,          setError]          = useState(null)

  const loadAll = useCallback(async () => {
    try {
      const [st, ps, g, gps] = await Promise.all([
        getSynergyStatus(),
        getSynergyPairs(),
        getSynergyGraph(),
        getSynergyGaps(),
      ])
      setStatus(st)
      setPairs(ps)
      setGraphData(g)
      setGaps(gps)
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => { loadAll() }, [loadAll])

  async function handleRun() {
    setRunning(true)
    setError(null)
    try {
      await runSynergy()
      await loadAll()
    } catch (e) {
      setError(e.message)
    } finally {
      setRunning(false)
    }
  }

  async function handleDetect(force = false) {
    setDetecting(true)
    setError(null)
    try {
      await detectSynergyGaps(force)
      const gps = await getSynergyGaps()
      setGaps(gps)
    } catch (e) {
      setError(e.message)
    } finally {
      setDetecting(false)
    }
  }

  async function handleHunt(gapId) {
    setError(null)
    try {
      const updated = await huntSynergyGap(gapId)
      setGaps(prev => prev.map(g => g.id === gapId ? updated : g))
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleDecide(pairId, { decision, reason }) {
    try {
      await decideSynergyPair(pairId, { decision, reason })
      await loadAll()
    } catch (e) {
      setError(e.message)
    }
  }

  function handleSelectPair(pairId) {
    setSelectedPairId(pairId)
    setTab('pairs')
  }

  const pendingCount = pairs.filter(p => p.analyst_decision === null).length

  return (
    <div style={{ padding: '32px 40px', maxWidth: 1200, margin: '0 auto' }}>

      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{
            fontFamily: 'Outfit, Inter, system-ui, sans-serif',
            fontSize: 28, fontWeight: 800, color: 'var(--tx-1)',
            margin: '0 0 6px', letterSpacing: '-0.02em',
          }}>
            Synergy Engine
          </h1>
          <p style={{ margin: 0, fontSize: 13, color: 'var(--tx-3)', lineHeight: 1.5 }}>
            Cross-portfolio synergy detection — service bridges, shared customers, co-development opportunities.
          </p>
        </div>
        <button
          onClick={handleRun}
          disabled={running}
          style={{
            padding: '9px 22px', borderRadius: 10, fontSize: 13, fontWeight: 700,
            cursor: running ? 'not-allowed' : 'pointer',
            background: running ? 'rgba(110,86,207,0.4)' : '#6E56CF',
            color: '#fff', border: 'none', transition: 'background 0.15s',
            display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0,
          }}
        >
          {running ? (
            <>
              <span style={{ display: 'inline-block', width: 14, height: 14, border: '2px solid rgba(255,255,255,0.4)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
              Analysing…
            </>
          ) : 'Run Analysis'}
        </button>
      </div>

      {/* ── Stat chips ── */}
      {status && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 28, flexWrap: 'wrap' }}>
          <STAT label="Profiles"      value={status.profiles_ready} />
          <STAT label="Pairs Scored"  value={status.pairs_computed} />
          <STAT label="Pending Review" value={pendingCount} color={pendingCount > 0 ? '#F5A524' : undefined} />
          <STAT label="Gaps Detected" value={status.gaps_detected} />
        </div>
      )}

      {/* ── Error ── */}
      {error && (
        <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: 10, padding: '10px 16px', marginBottom: 20, fontSize: 13, color: '#F04438' }}>
          {error}
        </div>
      )}

      {/* ── Tabs ── */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        <button style={TAB_STYLE(tab === 'pairs')} onClick={() => setTab('pairs')}>
          Synergy Pairs
          {pendingCount > 0 && (
            <span style={{ marginLeft: 7, background: '#6E56CF', color: '#fff', borderRadius: 10, padding: '1px 7px', fontSize: 10 }}>
              {pendingCount}
            </span>
          )}
        </button>
        <button style={TAB_STYLE(tab === 'graph')} onClick={() => setTab('graph')}>
          Network Graph
        </button>
        <button style={TAB_STYLE(tab === 'gaps')} onClick={() => setTab('gaps')}>
          Gap Intelligence
          <span style={{ marginLeft: 7, background: 'rgba(148,163,184,0.15)', color: 'var(--tx-3)', borderRadius: 10, padding: '1px 7px', fontSize: 9, fontFamily: 'JetBrains Mono, monospace' }}>
            S4
          </span>
        </button>
      </div>

      {/* ── Tab Content ── */}
      <AnimatePresence mode="wait">

        {tab === 'pairs' && (
          <motion.div key="pairs" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}>
            {pairs.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '64px 0', color: 'var(--tx-3)', fontSize: 14 }}>
                No pairs scored yet.{' '}
                <button onClick={handleRun} style={{ background: 'none', border: 'none', color: '#6E56CF', cursor: 'pointer', fontWeight: 600, fontSize: 14 }}>
                  Run Analysis →
                </button>
              </div>
            ) : (
              <SynergyPairTable
                pairs={pairs}
                onDecide={handleDecide}
                selectedPairId={selectedPairId}
              />
            )}
          </motion.div>
        )}

        {tab === 'graph' && (
          <motion.div key="graph" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}>
            <div style={{
              background: 'var(--surface-1)', border: '1px solid var(--border)',
              borderRadius: 16, overflow: 'hidden',
            }}>
              {graphData.nodes.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '64px 0', color: 'var(--tx-3)', fontSize: 14 }}>
                  No graph data.{' '}
                  <button onClick={handleRun} style={{ background: 'none', border: 'none', color: '#6E56CF', cursor: 'pointer', fontWeight: 600, fontSize: 14 }}>
                    Run Analysis →
                  </button>
                </div>
              ) : (
                <PortfolioGraph
                  nodes={graphData.nodes}
                  edges={graphData.edges}
                  onSelectPair={handleSelectPair}
                />
              )}
            </div>
            <p style={{ marginTop: 10, fontSize: 11, color: 'var(--tx-3)', textAlign: 'right', fontFamily: 'JetBrains Mono, monospace' }}>
              Click an edge to review the pair · Edges shown for composite ≥ 40
            </p>
          </motion.div>
        )}

        {tab === 'gaps' && (
          <motion.div key="gaps" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}>
            <GapPanel gaps={gaps} onDetect={handleDetect} detecting={detecting} onHunt={handleHunt} />
          </motion.div>
        )}

      </AnimatePresence>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
