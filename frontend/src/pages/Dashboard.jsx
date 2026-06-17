import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPipeline, getCompanySummary } from '../lib/api'
import ScorePill from '../components/shared/ScorePill'
import VerdictBadge from '../components/shared/VerdictBadge'
import ConfidenceBadge from '../components/shared/ConfidenceBadge'
import DeltaBadge from '../components/shared/DeltaBadge'

const COLUMNS = [
  { key: 'startup_name',    label: 'Company',    sortable: true  },
  { key: 'sector',          label: 'Sector',      sortable: true  },
  { key: 'stage',           label: 'Stage',       sortable: true  },
  { key: 'business_score',  label: 'Business',    sortable: true  },
  { key: 'esg_composite',   label: 'ESG',         sortable: true  },
  { key: 'conviction_delta',label: 'Δ Memory',    sortable: true  },
  { key: 'final_score',     label: 'Score',       sortable: true  },
  { key: 'decision',        label: 'Verdict',     sortable: false },
  { key: 'confidence_level',label: 'Confidence',  sortable: false },
  { key: 'compliance_health_score', label: 'Compliance', sortable: true  },
  { key: 'synergy',                label: 'Synergy',    sortable: false },
]

const COMPLIANCE_MAP = [
  { min: 75, color: '#12B76A', bg: 'rgba(18,183,106,0.1)'  },
  { min: 50, color: '#F5A524', bg: 'rgba(245,165,36,0.1)'  },
  { min: 25, color: '#EF6820', bg: 'rgba(239,104,32,0.1)'  },
  { min: 0,  color: '#F04438', bg: 'rgba(240,68,56,0.1)'   },
]

function CompliancePill({ score }) {
  if (score == null) return <span style={{ fontSize: 10, color: 'var(--tx-3)' }}>—</span>
  const { color, bg } = COMPLIANCE_MAP.find(c => score >= c.min) ?? COMPLIANCE_MAP[COMPLIANCE_MAP.length - 1]
  return (
    <span style={{
      fontFamily: 'JetBrains Mono, monospace',
      fontSize: 11, fontWeight: 700,
      color, background: bg,
      padding: '2px 7px', borderRadius: 6,
    }}>
      {score}
    </span>
  )
}

function SynergyChips({ summary, onClick }) {
  if (!summary) return <span style={{ fontSize: 10, color: 'var(--tx-3)' }}>—</span>
  const { approved_count, pending_count, gap_count } = summary
  if (!approved_count && !pending_count && !gap_count) {
    return <span style={{ fontSize: 10, color: 'var(--tx-3)' }}>—</span>
  }
  return (
    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }} onClick={e => { e.stopPropagation(); onClick() }}>
      {approved_count > 0 && (
        <span style={{
          fontSize: 9, padding: '1px 6px', borderRadius: 4, fontWeight: 700, cursor: 'pointer',
          background: 'rgba(34,197,94,0.1)', color: '#12B76A', border: '1px solid rgba(34,197,94,0.25)',
          fontFamily: 'JetBrains Mono, monospace',
        }}>
          ✓ {approved_count}
        </span>
      )}
      {pending_count > 0 && (
        <span style={{
          fontSize: 9, padding: '1px 6px', borderRadius: 4, fontWeight: 700, cursor: 'pointer',
          background: 'rgba(245,158,11,0.1)', color: '#F5A524', border: '1px solid rgba(245,158,11,0.25)',
          fontFamily: 'JetBrains Mono, monospace',
        }}>
          ~ {pending_count}
        </span>
      )}
      {gap_count > 0 && (
        <span style={{
          fontSize: 9, padding: '1px 6px', borderRadius: 4, fontWeight: 700, cursor: 'pointer',
          background: 'rgba(110,86,207,0.08)', color: '#6E56CF', border: '1px solid rgba(110,86,207,0.2)',
          fontFamily: 'JetBrains Mono, monospace',
        }}>
          ⚡ {gap_count}
        </span>
      )}
    </div>
  )
}

const STATS = [
  { label: 'Total',   filter: () => true,                                      color: 'var(--tx-1)'    },
  { label: 'Pursue',  filter: d => d.decision === 'pursue',                   color: 'var(--s-green)' },
  { label: 'Watch',   filter: d => d.decision === 'watch',                    color: 'var(--s-amber)' },
  { label: 'Pass',    filter: d => ['pass','soft_pass'].includes(d.decision), color: 'var(--s-red)'   },
]

function SkeletonRow() {
  return (
    <tr>
      {COLUMNS.map((_, i) => (
        <td key={i} style={{ padding: '14px 16px', borderBottom: '1px solid var(--border)' }}>
          <div
            className="skeleton"
            style={{
              height:       13,
              borderRadius: 6,
              background:   'rgba(16, 19, 24, 0.06)',
              width:        `${45 + (i * 11) % 40}%`,
            }}
          />
        </td>
      ))}
    </tr>
  )
}

function SortArrow({ dir }) {
  if (!dir) return <span style={{ color: 'var(--tx-3)', marginLeft: 4, fontSize: 10 }}>↕</span>
  return <span style={{ color: 'var(--gold)', marginLeft: 4, fontSize: 10 }}>{dir === 'asc' ? '↑' : '↓'}</span>
}

export default function Dashboard({ refreshKey = 0 }) {
  const [deals, setDeals]               = useState([])
  const [loading, setLoading]           = useState(true)
  const [error, setError]               = useState(null)
  const [sort, setSort]                 = useState({ key: 'final_score', dir: 'desc' })
  const [hoveredRow, setHoveredRow]     = useState(null)
  const [synergySummaries, setSynergySummaries] = useState({})
  const navigate = useNavigate()

  useEffect(() => {
    setLoading(true)
    getPipeline()
      .then(data => {
        setDeals(data)
        setLoading(false)
        // Fetch synergy summaries in parallel — failures silently leave cell as "—"
        Promise.allSettled(data.map(d => getCompanySummary(d.startup_name)))
          .then(results => {
            const map = {}
            results.forEach((r, i) => {
              if (r.status === 'fulfilled') map[data[i].startup_name] = r.value
            })
            setSynergySummaries(map)
          })
      })
      .catch(() => { setError('Backend not reachable — start uvicorn first.'); setLoading(false) })
  }, [refreshKey])

  const sorted = useMemo(() => {
    if (!sort.key) return deals
    return [...deals].sort((a, b) => {
      const av = a[sort.key] ?? -Infinity
      const bv = b[sort.key] ?? -Infinity
      const cmp = typeof av === 'string' ? av.localeCompare(bv) : av - bv
      return sort.dir === 'asc' ? cmp : -cmp
    })
  }, [deals, sort])

  const toggleSort = key =>
    setSort(prev =>
      prev.key === key
        ? { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' }
        : { key, dir: 'desc' }
    )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>

      {/* ── Page header ── */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
        <div>
          <h1
            style={{
              fontFamily:    "'Outfit', 'Inter', system-ui, sans-serif",
              fontSize:      36,
              fontWeight:    700,
              color:         'var(--tx-1)',
              margin:        0,
              letterSpacing: '-0.02em',
              lineHeight:    1,
            }}
          >
            Pipeline
          </h1>
          <p style={{ fontSize: 13, color: 'var(--tx-3)', marginTop: 8, marginBottom: 0 }}>
            {loading
              ? 'Loading…'
              : `${deals.length} startup${deals.length !== 1 ? 's' : ''} under review`}
          </p>
        </div>

        <button
          onClick={() => navigate('/evaluate')}
          onMouseEnter={e => (e.currentTarget.style.opacity = '0.88')}
          onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
          style={{
            display:       'flex',
            alignItems:    'center',
            gap:           7,
            padding:       '9px 18px',
            borderRadius:  10,
            background:    'linear-gradient(135deg, #6E56CF 0%, #8B7CFF 100%)',
            color:         '#FFFFFF',
            fontSize:      13,
            fontWeight:    600,
            border:        'none',
            cursor:        'pointer',
            transition:    'opacity 0.15s',
            letterSpacing: '0.01em',
            boxShadow:     '0 2px 8px rgba(110, 86, 207, 0.28)',
          }}
        >
          <span style={{ fontSize: 18, lineHeight: 1, marginTop: -1 }}>+</span>
          New Evaluation
        </button>
      </div>

      {/* ── Error ── */}
      {error && (
        <div
          style={{
            background:   'rgba(240,68,56,0.06)',
            border:       '1px solid rgba(240,68,56,0.22)',
            borderRadius: 12,
            padding:      '12px 18px',
            fontSize:     13,
            color:        'var(--s-red)',
          }}
        >
          {error}
        </div>
      )}

      {/* ── Stat cards ── */}
      {!loading && !error && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12 }}>
          {STATS.map(({ label, filter, color }) => (
            <div
              key={label}
              style={{
                background:   'var(--surface-1)',
                border:       '1px solid var(--border)',
                borderRadius: 16,
                padding:      '20px 24px',
                boxShadow:    '0 1px 3px rgba(16,24,40,0.06)',
              }}
            >
              <p
                style={{
                  fontSize:      10,
                  color:         'var(--tx-3)',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  fontWeight:    500,
                  margin:        0,
                }}
              >
                {label}
              </p>
              <p
                style={{
                  fontFamily:    'JetBrains Mono, monospace',
                  fontSize:      38,
                  fontWeight:    700,
                  color,
                  margin:        '8px 0 0 0',
                  letterSpacing: '-0.04em',
                  lineHeight:    1,
                }}
              >
                {deals.filter(filter).length}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* ── Table ── */}
      <div
        style={{
          background:   'var(--surface-1)',
          border:       '1px solid var(--border)',
          borderRadius: 20,
          overflow:     'hidden',
          boxShadow:    '0 1px 3px rgba(16,24,40,0.06)',
        }}
      >
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr>
                {COLUMNS.map(col => (
                  <th
                    key={col.key}
                    onClick={() => col.sortable && toggleSort(col.key)}
                    style={{
                      padding:       '12px 16px',
                      textAlign:     'left',
                      fontSize:      10,
                      fontWeight:    500,
                      color:         sort.key === col.key ? 'var(--gold)' : 'var(--tx-3)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.09em',
                      whiteSpace:    'nowrap',
                      cursor:        col.sortable ? 'pointer' : 'default',
                      userSelect:    'none',
                      transition:    'color 0.15s',
                      background:    'var(--surface-2)',
                      borderBottom:  '1px solid var(--border)',
                    }}
                  >
                    {col.label}
                    {col.sortable && <SortArrow dir={sort.key === col.key ? sort.dir : null} />}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading
                ? Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)
                : sorted.map((deal, idx) => {
                    const hovered = hoveredRow === idx
                    return (
                      <tr
                        key={deal.id}
                        onClick={() => navigate(`/evaluate?cached=${encodeURIComponent(deal.startup_name)}`)}
                        onMouseEnter={() => setHoveredRow(idx)}
                        onMouseLeave={() => setHoveredRow(null)}
                        style={{
                          cursor:       'pointer',
                          background:   hovered ? 'rgba(110, 86, 207, 0.04)' : 'transparent',
                          transition:   'background 0.12s',
                          borderBottom: '1px solid var(--border)',
                        }}
                      >
                        {/* Company name */}
                        <td style={{ padding: '14px 16px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span
                              style={{
                                display:      'block',
                                width:        2,
                                height:       16,
                                borderRadius: 1,
                                background:   hovered ? 'var(--gold)' : 'transparent',
                                flexShrink:   0,
                                transition:   'background 0.15s',
                              }}
                            />
                            <span style={{ fontWeight: 600, color: 'var(--tx-1)', letterSpacing: '-0.01em' }}>
                              {deal.startup_name}
                            </span>
                          </div>
                        </td>

                        <td style={{ padding: '14px 16px', color: 'var(--tx-2)' }}>{deal.sector}</td>

                        <td style={{ padding: '14px 16px' }}>
                          <span
                            style={{
                              fontSize:     11,
                              fontWeight:   500,
                              color:        'var(--tx-2)',
                              background:   'var(--surface-2)',
                              border:       '1px solid var(--border)',
                              padding:      '2px 8px',
                              borderRadius: 6,
                            }}
                          >
                            {deal.stage}
                          </span>
                        </td>

                        <td style={{ padding: '14px 16px' }}><ScorePill score={deal.business_score} /></td>
                        <td style={{ padding: '14px 16px' }}><ScorePill score={deal.esg_composite} /></td>
                        <td style={{ padding: '14px 16px' }}><DeltaBadge delta={deal.conviction_delta} /></td>
                        <td style={{ padding: '14px 16px' }}><ScorePill score={deal.final_score} /></td>
                        <td style={{ padding: '14px 16px' }}><VerdictBadge decision={deal.decision} /></td>
                        <td style={{ padding: '14px 16px' }}><ConfidenceBadge level={deal.confidence_level} /></td>
                        <td style={{ padding: '14px 16px' }}><CompliancePill score={deal.compliance_health_score} /></td>
                        <td style={{ padding: '14px 16px' }}>
                          <SynergyChips
                            summary={synergySummaries[deal.startup_name]}
                            onClick={() => navigate('/synergy')}
                          />
                        </td>
                      </tr>
                    )
                  })
              }
            </tbody>
          </table>
        </div>

        {!loading && !error && deals.length === 0 && (
          <div style={{ padding: '52px 0', textAlign: 'center', color: 'var(--tx-3)', fontSize: 13 }}>
            No pipeline startups yet.{' '}
            <button
              onClick={() => navigate('/evaluate')}
              style={{
                color:          'var(--gold)',
                background:     'none',
                border:         'none',
                cursor:         'pointer',
                textDecoration: 'underline',
                fontSize:       13,
              }}
            >
              Add one →
            </button>
          </div>
        )}
      </div>

      {/* ── Score legend ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        <span
          style={{
            fontSize:      10,
            fontWeight:    500,
            color:         'var(--tx-3)',
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
          }}
        >
          Score
        </span>
        {[
          { range: '75–100', color: 'var(--s-green)'  },
          { range: '60–74',  color: 'var(--s-amber)'  },
          { range: '45–59',  color: 'var(--s-orange)' },
          { range: '0–44',   color: 'var(--s-red)'    },
        ].map(({ range, color }) => (
          <span key={range} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: 'var(--tx-3)' }}>
              {range}
            </span>
          </span>
        ))}
      </div>

    </div>
  )
}
