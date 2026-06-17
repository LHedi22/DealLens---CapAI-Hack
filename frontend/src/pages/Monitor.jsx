import { useState, useEffect, useCallback } from 'react'
import ComplianceDashboard from '../components/monitor/ComplianceDashboard'
import ComplianceHealthBadge from '../components/monitor/ComplianceHealthBadge'
import TransactionLog from '../components/monitor/TransactionLog'
import StatementUploader from '../components/monitor/StatementUploader'
import BudgetTracker from '../components/monitor/BudgetTracker'
import AlertPanel from '../components/monitor/AlertPanel'
import TimelineChart from '../components/monitor/TimelineChart'

const API = 'http://localhost:8000'

function SmallHealthDot({ score }) {
  const color =
    score == null ? '#D0D4DC' :
    score >= 75   ? '#12B76A' :
    score >= 50   ? '#F5A524' :
    score >= 25   ? '#EF6820' :
                    '#F04438'
  return (
    <span
      style={{
        display: 'inline-block', width: 7, height: 7,
        borderRadius: '50%', background: color, flexShrink: 0,
      }}
    />
  )
}

const TABS = [
  { key: 'overview',     label: 'Overview'      },
  { key: 'budget',       label: 'Budget'        },
  { key: 'transactions', label: 'Transactions'  },
  { key: 'alerts',       label: 'Alerts'        },
  { key: 'timeline',     label: 'Timeline'      },
]

export default function Monitor() {
  const [startups, setStartups]   = useState([])
  const [selected, setSelected]   = useState('BuildSmart')
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading]     = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [txRefreshKey, setTxRefreshKey] = useState(0)

  useEffect(() => {
    fetch(`${API}/api/monitor/portfolio-health`)
      .then(r => r.json())
      .then(data => setStartups(data.monitored_startups ?? []))
      .catch(() => {})
  }, [])

  const fetchDashboard = useCallback((name) => {
    setLoading(true)
    setDashboard(null)
    fetch(`${API}/api/monitor/dashboard/${encodeURIComponent(name)}`)
      .then(r => r.json())
      .then(data => { setDashboard(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selected) return
    fetchDashboard(selected)
  }, [selected, fetchDashboard])

  function handleStatementUploaded() {
    fetchDashboard(selected)
    setTxRefreshKey(k => k + 1)
    fetch(`${API}/api/monitor/portfolio-health`)
      .then(r => r.json())
      .then(data => setStartups(data.monitored_startups ?? []))
      .catch(() => {})
  }

  const criticalAlerts = dashboard?.active_alerts?.filter(a => a.severity === 'CRITICAL') ?? []

  return (
    <div style={{ display: 'flex', gap: 24, minHeight: 'calc(100vh - 8rem)' }}>

      {/* ── Sidebar ── */}
      <aside style={{ width: 220, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
        <p style={{
          fontSize: 10, fontWeight: 600, color: 'var(--tx-3)',
          letterSpacing: '0.10em', textTransform: 'uppercase', marginBottom: 4,
        }}>
          Monitored Startups
        </p>

        {startups.length === 0 && (
          <p style={{ fontSize: 12, color: 'var(--tx-3)', marginTop: 8 }}>
            No monitored startups yet.
          </p>
        )}

        {startups.map(s => {
          const isActive = selected === s.startup_name
          return (
            <button
              key={s.startup_name}
              onClick={() => { setSelected(s.startup_name); setActiveTab('overview') }}
              style={{
                textAlign:    'left',
                padding:      '10px 12px',
                borderRadius: 12,
                border:       isActive ? '1px solid rgba(110,86,207,0.25)' : '1px solid var(--border)',
                background:   isActive ? 'rgba(110,86,207,0.08)' : 'var(--surface-1)',
                cursor:       'pointer',
                transition:   'all 0.15s',
              }}
            >
              <div style={{
                fontSize: 13, fontWeight: 600,
                color: isActive ? '#6E56CF' : 'var(--tx-1)',
              }}>
                {s.startup_name}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 5 }}>
                <SmallHealthDot score={s.compliance_health_score} />
                <span style={{ fontSize: 11, color: 'var(--tx-3)' }}>
                  {s.compliance_health_score ?? '—'} / 100
                </span>
                {s.alert_count_active > 0 && (
                  <span style={{
                    marginLeft: 'auto', fontSize: 10, fontWeight: 700,
                    color: '#FFFFFF', background: '#F04438',
                    padding: '1px 6px', borderRadius: 5,
                  }}>
                    {s.alert_count_active}
                  </span>
                )}
              </div>
            </button>
          )
        })}
      </aside>

      {/* ── Main panel ── */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 16 }}>

        {/* Critical alert banner */}
        {criticalAlerts.length > 0 && (
          <div style={{
            background:   'rgba(240,68,56,0.06)',
            border:       '1px solid rgba(240,68,56,0.22)',
            borderRadius: 12,
            padding:      '12px 16px',
          }}>
            <p style={{ fontSize: 13, fontWeight: 600, color: '#DC2626', margin: '0 0 4px' }}>
              {criticalAlerts.length} Critical Alert{criticalAlerts.length > 1 ? 's' : ''}
            </p>
            {criticalAlerts.map((a, i) => (
              <p key={i} style={{ fontSize: 12, color: '#F04438', lineHeight: 1.5, margin: 0 }}>
                {a.alert_summary}
              </p>
            ))}
          </div>
        )}

        {/* Tab bar */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', gap: 0 }}>
          {TABS.map(tab => {
            const isActive = activeTab === tab.key
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  padding:      '10px 16px',
                  fontSize:     13,
                  fontWeight:   isActive ? 600 : 400,
                  color:        isActive ? '#6E56CF' : 'var(--tx-3)',
                  background:   'none',
                  border:       'none',
                  borderBottom: isActive ? '2px solid #6E56CF' : '2px solid transparent',
                  marginBottom: -1,
                  cursor:       'pointer',
                  transition:   'color 0.15s',
                  display:      'flex',
                  alignItems:   'center',
                  gap:          6,
                }}
              >
                {tab.label}
                {tab.key === 'alerts' && (dashboard?.alert_count_active ?? 0) > 0 && (
                  <span style={{
                    fontSize: 10, fontWeight: 700,
                    background: '#F04438', color: '#FFFFFF',
                    padding: '0 5px', borderRadius: 4,
                  }}>
                    {dashboard.alert_count_active}
                  </span>
                )}
              </button>
            )
          })}
        </div>

        {/* Tab content */}
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '80px 0', color: 'var(--tx-3)', fontSize: 13 }}>
            Loading…
          </div>
        ) : (
          <>
            {activeTab === 'overview' && <ComplianceDashboard dashboard={dashboard} />}
            {activeTab === 'budget'   && <BudgetTracker categoryTotals={dashboard?.category_totals} />}
            {activeTab === 'transactions' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                <StatementUploader startupName={selected} onUploaded={handleStatementUploaded} />
                <TransactionLog startupName={selected} refreshKey={txRefreshKey} />
              </div>
            )}
            {activeTab === 'alerts' && (
              <AlertPanel
                startupName={selected}
                onHealthChanged={() => {
                  fetchDashboard(selected)
                  fetch(`${API}/api/monitor/portfolio-health`)
                    .then(r => r.json())
                    .then(data => setStartups(data.monitored_startups ?? []))
                    .catch(() => {})
                }}
              />
            )}
            {activeTab === 'timeline' && <TimelineChart startupName={selected} />}
          </>
        )}
      </div>
    </div>
  )
}
