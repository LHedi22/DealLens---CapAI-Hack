import { useState, useEffect, useCallback } from 'react'
import { getMonitorTransactions, reclassifyTransaction } from '../../lib/api'

const CATEGORIES = ['rd', 'construction', 'equipment', 'salaries', 'working_capital', 'marketing', 'training', 'other']

const CATEGORY_LABELS = {
  rd: 'R&D', construction: 'Construction', equipment: 'Equipment',
  salaries: 'Salaries', working_capital: 'Working Capital',
  marketing: 'Marketing', training: 'Training', other: 'Other',
}

const STATUS_STYLE = {
  AUTO_CLASSIFIED: { bg: 'rgba(78,140,255,0.10)', color: '#1E40AF', border: 'rgba(78,140,255,0.25)' },
  HUMAN_VERIFIED:  { bg: 'rgba(18,183,106,0.10)', color: '#065F46', border: 'rgba(18,183,106,0.25)' },
  UNCLASSIFIED:    { bg: 'rgba(240,68,56,0.10)',  color: '#991B1B', border: 'rgba(240,68,56,0.25)'  },
}

const ALERT_STYLE = {
  OFF_PLAN:    { bg: 'rgba(240,68,56,0.10)',  color: '#991B1B', border: 'rgba(240,68,56,0.25)'  },
  OVER_BUDGET: { bg: 'rgba(240,68,56,0.10)',  color: '#991B1B', border: 'rgba(240,68,56,0.25)'  },
}

const PAGE_SIZE = 50

function CategoryBadge({ tx, onReclassify }) {
  const [open, setOpen]   = useState(false)
  const [saving, setSaving] = useState(false)

  const effective       = tx.human_category || tx.ai_category
  const isUnclassified  = tx.classification_status === 'UNCLASSIFIED'

  async function handleSelect(cat) {
    setSaving(true)
    try {
      const data = await reclassifyTransaction(tx.id, cat)
      onReclassify(tx.id, cat, data.compliance_health_score)
    } catch {
      // ignore
    } finally {
      setSaving(false)
      setOpen(false)
    }
  }

  if (!isUnclassified) {
    return (
      <span style={{
        padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 500,
        background: 'var(--surface-2)', color: 'var(--tx-2)',
        border: '1px solid var(--border)',
      }}>
        {CATEGORY_LABELS[effective] || effective || '—'}
      </span>
    )
  }

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setOpen(o => !o)}
        disabled={saving}
        style={{
          padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 700,
          background: 'rgba(240,68,56,0.10)', color: '#991B1B',
          border: '1px solid rgba(240,68,56,0.30)',
          cursor: saving ? 'not-allowed' : 'pointer',
          transition: 'border-color 0.15s',
        }}
      >
        {saving ? 'Saving…' : 'UNCLASSIFIED ▾'}
      </button>
      {open && (
        <div style={{
          position: 'absolute', zIndex: 50, top: 28, left: 0,
          background: 'var(--surface-1)', border: '1px solid var(--border)',
          borderRadius: 10, boxShadow: '0 4px 16px rgba(16,24,40,0.12)',
          minWidth: 160, overflow: 'hidden',
        }}>
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              onClick={() => handleSelect(cat)}
              style={{
                display: 'block', width: '100%', textAlign: 'left',
                padding: '8px 12px', fontSize: 12, color: 'var(--tx-2)',
                background: 'none', border: 'none', cursor: 'pointer',
                transition: 'background 0.1s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-2)'}
              onMouseLeave={e => e.currentTarget.style.background = 'none'}
            >
              {CATEGORY_LABELS[cat]}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function TransactionLog({ startupName, refreshKey = 0 }) {
  const [txs, setTxs]               = useState([])
  const [total, setTotal]           = useState(0)
  const [page, setPage]             = useState(1)
  const [loading, setLoading]       = useState(false)
  const [filterCat, setFilterCat]   = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterMonth, setFilterMonth]   = useState('')

  const load = useCallback(async () => {
    if (!startupName) return
    setLoading(true)
    try {
      const data = await getMonitorTransactions(startupName, {
        page, pageSize: PAGE_SIZE,
        category: filterCat, status: filterStatus, month: filterMonth,
      })
      setTxs(data.transactions || [])
      setTotal(data.total || 0)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [startupName, page, filterCat, filterStatus, filterMonth, refreshKey])

  useEffect(() => { load() }, [load])
  useEffect(() => { setPage(1) }, [startupName, filterCat, filterStatus, filterMonth, refreshKey])

  function handleReclassify(txId, newCat) {
    setTxs(prev => prev.map(tx =>
      tx.id === txId
        ? { ...tx, human_category: newCat, classification_status: 'HUMAN_VERIFIED', alert_triggered: 0, alert_type: null }
        : tx
    ))
  }

  const hasFilters = filterCat || filterStatus || filterMonth

  const selectStyle = {
    background: 'var(--surface-1)', border: '1px solid var(--border)',
    color: 'var(--tx-2)', fontSize: 12, borderRadius: 8, padding: '6px 10px',
    outline: 'none',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

      {/* Filter bar */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <select value={filterCat} onChange={e => setFilterCat(e.target.value)} style={selectStyle}>
          <option value="">All categories</option>
          {CATEGORIES.map(c => <option key={c} value={c}>{CATEGORY_LABELS[c]}</option>)}
        </select>

        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={selectStyle}>
          <option value="">All statuses</option>
          <option value="AUTO_CLASSIFIED">Auto-classified</option>
          <option value="HUMAN_VERIFIED">Human verified</option>
          <option value="UNCLASSIFIED">Unclassified</option>
        </select>

        <input
          type="month"
          value={filterMonth}
          onChange={e => setFilterMonth(e.target.value)}
          style={selectStyle}
        />

        {hasFilters && (
          <button
            onClick={() => { setFilterCat(''); setFilterStatus(''); setFilterMonth('') }}
            style={{ fontSize: 12, color: 'var(--tx-3)', background: 'none', border: 'none', cursor: 'pointer', transition: 'color 0.15s' }}
          >
            Clear filters
          </button>
        )}

        <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--tx-3)', fontFamily: 'JetBrains Mono, monospace' }}>
          {total} transaction{total !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Table */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--tx-3)', fontSize: 13 }}>Loading transactions…</div>
      ) : txs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--tx-3)', fontSize: 13 }}>
          {hasFilters ? 'No transactions match the current filters.' : 'No transactions uploaded yet.'}
        </div>
      ) : (
        <div style={{ overflowX: 'auto', borderRadius: 14, border: '1px solid var(--border)', boxShadow: '0 1px 3px rgba(16,24,40,0.06)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', background: 'var(--surface-2)', textAlign: 'left' }}>
                {['Date', 'Beneficiary', 'Amount (TND)', 'Memo', 'Category', 'Status', 'Alert'].map((h, i) => (
                  <th key={h} style={{
                    padding: '10px 12px', fontSize: 10, fontWeight: 600,
                    color: 'var(--tx-3)', textTransform: 'uppercase', letterSpacing: '0.08em',
                    textAlign: i === 2 ? 'right' : 'left',
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {txs.map(tx => {
                const isUnclassified = tx.classification_status === 'UNCLASSIFIED'
                return (
                  <tr
                    key={tx.id}
                    style={{
                      borderBottom: '1px solid var(--border)',
                      background: isUnclassified ? 'rgba(240,68,56,0.03)' : 'transparent',
                      transition: 'background 0.12s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = isUnclassified ? 'rgba(240,68,56,0.05)' : 'rgba(110,86,207,0.03)'}
                    onMouseLeave={e => e.currentTarget.style.background = isUnclassified ? 'rgba(240,68,56,0.03)' : 'transparent'}
                  >
                    <td style={{ padding: '10px 12px', color: 'var(--tx-3)', whiteSpace: 'nowrap', fontFamily: 'JetBrains Mono, monospace', fontSize: 11 }}>
                      {tx.transaction_date || '—'}
                    </td>
                    <td style={{ padding: '10px 12px', color: 'var(--tx-1)', fontWeight: 600, maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {tx.beneficiary || '—'}
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'JetBrains Mono, monospace', color: 'var(--tx-1)', fontWeight: 600, whiteSpace: 'nowrap' }}>
                      {tx.amount_tnd != null ? tx.amount_tnd.toLocaleString('fr-TN', { minimumFractionDigits: 3 }) : '—'}
                    </td>
                    <td style={{ padding: '10px 12px', color: 'var(--tx-3)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={tx.memo}>
                      {tx.memo || '—'}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <CategoryBadge tx={tx} onReclassify={handleReclassify} />
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      {(() => {
                        const s = STATUS_STYLE[tx.classification_status]
                        if (!s) return <span style={{ color: 'var(--tx-3)' }}>—</span>
                        return (
                          <span style={{
                            fontSize: 10, fontWeight: 600, padding: '2px 6px', borderRadius: 5,
                            background: s.bg, color: s.color, border: `1px solid ${s.border}`,
                            fontFamily: 'JetBrains Mono, monospace',
                          }}>
                            {tx.classification_status}
                          </span>
                        )
                      })()}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      {tx.alert_type ? (() => {
                        const a = ALERT_STYLE[tx.alert_type] || { bg: 'rgba(245,165,36,0.10)', color: '#92400E', border: 'rgba(245,165,36,0.25)' }
                        return (
                          <span style={{
                            fontSize: 10, fontWeight: 600, padding: '2px 6px', borderRadius: 5,
                            background: a.bg, color: a.color, border: `1px solid ${a.border}`,
                            fontFamily: 'JetBrains Mono, monospace',
                          }}>
                            {tx.alert_type}
                          </span>
                        )
                      })() : (
                        <span style={{ color: 'var(--border)', fontSize: 12 }}>—</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {total > PAGE_SIZE && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 12, marginTop: 4 }}>
          <button
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            style={{
              fontSize: 12, padding: '6px 12px', borderRadius: 8,
              background: 'var(--surface-2)', color: 'var(--tx-2)',
              border: '1px solid var(--border)', cursor: page === 1 ? 'not-allowed' : 'pointer',
              opacity: page === 1 ? 0.4 : 1, transition: 'all 0.15s',
            }}
          >
            ← Prev
          </button>
          <span style={{ fontSize: 12, color: 'var(--tx-3)', fontFamily: 'JetBrains Mono, monospace' }}>
            Page {page} of {Math.ceil(total / PAGE_SIZE)}
          </span>
          <button
            disabled={page >= Math.ceil(total / PAGE_SIZE)}
            onClick={() => setPage(p => p + 1)}
            style={{
              fontSize: 12, padding: '6px 12px', borderRadius: 8,
              background: 'var(--surface-2)', color: 'var(--tx-2)',
              border: '1px solid var(--border)',
              cursor: page >= Math.ceil(total / PAGE_SIZE) ? 'not-allowed' : 'pointer',
              opacity: page >= Math.ceil(total / PAGE_SIZE) ? 0.4 : 1, transition: 'all 0.15s',
            }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}
