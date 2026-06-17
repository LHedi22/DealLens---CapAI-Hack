import { useState } from 'react'

const CX = 400
const CY = 210
const R  = 155

const SECTOR_COLORS = {
  'EdTech':            '#8B5CF6',
  'FinTech':           '#3B82F6',
  'Logistics':         '#F5A524',
  'HealthTech':        '#12B76A',
  'Construction Tech': '#EF6820',
}

function edgeColor(types = []) {
  if (types.length > 1) return '#a855f7'
  if (types[0] === 'SERVICE')  return '#3b82f6'
  if (types[0] === 'CUSTOMER') return '#12B76A'
  if (types[0] === 'CO_DEV')   return '#EF6820'
  return '#94a3b8'
}

function nodePositions(nodes) {
  return nodes.map((n, i) => {
    const angle = (-Math.PI / 2) + (2 * Math.PI * i / nodes.length)
    return { ...n, x: CX + R * Math.cos(angle), y: CY + R * Math.sin(angle) }
  })
}

export default function PortfolioGraph({ nodes = [], edges = [], onSelectPair }) {
  const [hoveredNode, setHoveredNode]  = useState(null)
  const [hoveredEdge, setHoveredEdge]  = useState(null)
  const positioned = nodePositions(nodes)
  const nodeMap    = Object.fromEntries(positioned.map(n => [n.id, n]))

  const visibleEdges = edges.filter(e => e.analyst_decision !== 'rejected')

  function isConnected(nodeId) {
    if (!hoveredNode) return true
    if (nodeId === hoveredNode) return true
    return visibleEdges.some(
      e => (e.source === hoveredNode && e.target === nodeId) ||
           (e.target === hoveredNode && e.source === nodeId)
    )
  }

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <svg
        viewBox="0 0 800 420"
        style={{ width: '100%', height: 'auto', display: 'block' }}
        preserveAspectRatio="xMidYMid meet"
      >
        {/* ── Edges ── */}
        {visibleEdges.map(edge => {
          const src  = nodeMap[edge.source]
          const tgt  = nodeMap[edge.target]
          if (!src || !tgt) return null

          const isPending  = edge.analyst_decision === null
          const isApproved = edge.analyst_decision === 'approved'
          const color      = edgeColor(edge.types || [])
          const thickness  = Math.max(1.5, (edge.composite_score || 0) / 20)
          const isHov      = hoveredEdge === edge.pair_id
          const faded      = hoveredNode && !isConnected(edge.source) && !isConnected(edge.target)

          return (
            <line
              key={edge.pair_id}
              x1={src.x} y1={src.y}
              x2={tgt.x} y2={tgt.y}
              stroke={isHov ? '#ffffff' : color}
              strokeWidth={isHov ? thickness + 1.5 : thickness}
              strokeDasharray={isPending ? '6 4' : undefined}
              strokeOpacity={faded ? 0.1 : isHov ? 1 : isApproved ? 0.85 : 0.55}
              style={{ cursor: 'pointer', transition: 'stroke-opacity 0.2s' }}
              onMouseEnter={() => setHoveredEdge(edge.pair_id)}
              onMouseLeave={() => setHoveredEdge(null)}
              onClick={() => onSelectPair && onSelectPair(edge.pair_id)}
            />
          )
        })}

        {/* ── Score label on hovered edge ── */}
        {hoveredEdge && (() => {
          const edge = visibleEdges.find(e => e.pair_id === hoveredEdge)
          if (!edge) return null
          const src = nodeMap[edge.source]
          const tgt = nodeMap[edge.target]
          if (!src || !tgt) return null
          const mx = (src.x + tgt.x) / 2
          const my = (src.y + tgt.y) / 2
          return (
            <g key="edge-label">
              <rect x={mx - 16} y={my - 10} width={32} height={18} rx={4}
                fill="var(--surface-1)" stroke="var(--border)" strokeWidth={1} />
              <text x={mx} y={my + 4} textAnchor="middle"
                fill="var(--tx-1)" fontSize={11} fontFamily="JetBrains Mono, monospace" fontWeight={700}>
                {edge.composite_score}
              </text>
            </g>
          )
        })()}

        {/* ── Nodes ── */}
        {positioned.map(node => {
          const color  = SECTOR_COLORS[node.sector] || '#94a3b8'
          const faded  = hoveredNode && hoveredNode !== node.id && !isConnected(node.id)
          const active = hoveredNode === node.id

          return (
            <g
              key={node.id}
              style={{ cursor: 'pointer', transition: 'opacity 0.2s' }}
              opacity={faded ? 0.25 : 1}
              onMouseEnter={() => setHoveredNode(node.id)}
              onMouseLeave={() => setHoveredNode(null)}
            >
              {/* Outer glow ring */}
              {active && (
                <circle cx={node.x} cy={node.y} r={28}
                  fill="none" stroke={color} strokeWidth={2} strokeOpacity={0.35} />
              )}
              {/* Node circle */}
              <circle cx={node.x} cy={node.y} r={22}
                fill={`${color}22`} stroke={color} strokeWidth={active ? 2.5 : 1.5} />
              {/* Initials */}
              <text x={node.x} y={node.y + 1} textAnchor="middle" dominantBaseline="middle"
                fill={color} fontSize={10} fontFamily="JetBrains Mono, monospace" fontWeight={700}>
                {node.id.slice(0, 3).toUpperCase()}
              </text>
              {/* Company label */}
              <text x={node.x} y={node.y + 36} textAnchor="middle"
                fill="var(--tx-1)" fontSize={11} fontFamily="Outfit, Inter, system-ui, sans-serif" fontWeight={600}>
                {node.id}
              </text>
              {/* Stage label */}
              <text x={node.x} y={node.y + 50} textAnchor="middle"
                fill="var(--tx-3)" fontSize={9} fontFamily="JetBrains Mono, monospace">
                {node.stage}
              </text>
            </g>
          )
        })}
      </svg>

      {/* ── Legend ── */}
      <div style={{
        position: 'absolute', bottom: 8, right: 12,
        display: 'flex', flexDirection: 'column', gap: 5,
      }}>
        {[
          { color: '#3b82f6', label: 'Service Bridge' },
          { color: '#12B76A', label: 'Shared Customer' },
          { color: '#EF6820', label: 'Co-Dev' },
          { color: '#a855f7', label: 'Multi-type' },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 20, height: 2.5, background: color, borderRadius: 2 }} />
            <span style={{ fontSize: 9, color: 'var(--tx-3)', fontFamily: 'JetBrains Mono, monospace' }}>{label}</span>
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginTop: 2 }}>
          <svg width={20} height={4}>
            <line x1={0} y1={2} x2={20} y2={2} stroke="var(--tx-3)" strokeWidth={1.5} strokeDasharray="4 3" />
          </svg>
          <span style={{ fontSize: 9, color: 'var(--tx-3)', fontFamily: 'JetBrains Mono, monospace' }}>Pending</span>
        </div>
      </div>
    </div>
  )
}
