import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Evaluate from './pages/Evaluate'
import Mandate from './pages/Mandate'
import Monitor from './pages/Monitor'
import Synergy from './pages/Synergy'
import Debug from './pages/Debug'
import { getSynergyStatus, getMonitorCriticalCount } from './lib/api'

function usePendingSynergy() {
  const [count, setCount] = useState(0)
  useEffect(() => {
    getSynergyStatus()
      .then(s => setCount(s.pending_pairs ?? 0))
      .catch(() => {})
  }, [])
  return count
}

function useCriticalAlerts() {
  const [count, setCount] = useState(0)
  useEffect(() => {
    const fetch = async () => {
      const n = await getMonitorCriticalCount()
      setCount(n)
    }
    fetch()
    const interval = setInterval(fetch, 30000)
    return () => clearInterval(interval)
  }, [])
  return count
}

const NAV_ITEMS = [
  { to: '/',         label: 'Dashboard',      end: true  },
  { to: '/evaluate', label: 'New Evaluation', end: false },
  { to: '/monitor',  label: 'Monitor',        end: false },
  { to: '/synergy',  label: 'Synergy',        end: false },
  { to: '/mandate',  label: 'Fund Mandate',   end: false },
  { to: '/debug',    label: 'Debug',          end: false },
]

function LogoMark() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
      <circle cx="11" cy="4.5" r="2.8" fill="#6E56CF" />
      <circle cx="4.5" cy="16.5" r="2.8" fill="#8B7CFF" />
      <circle cx="17.5" cy="16.5" r="2.8" fill="#B8A9FF" />
      <line x1="11" y1="7.3" x2="4.5" y2="13.7" stroke="#6E56CF" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="11" y1="7.3" x2="17.5" y2="13.7" stroke="#6E56CF" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="4.5" y1="16.5" x2="17.5" y2="16.5" stroke="#B8A9FF" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  )
}

function Sidebar({ pendingSynergy = 0, criticalCount = 0 }) {
  return (
    <aside
      className="fixed left-0 top-0 h-screen flex flex-col z-50 overflow-hidden"
      style={{
        width:       220,
        background:  '#FFFFFF',
        borderRight: '1px solid var(--border)',
      }}
    >
      {/* Logo */}
      <div
        className="flex items-center gap-3 px-5 shrink-0 select-none"
        style={{ height: 64, borderBottom: '1px solid var(--border)' }}
      >
        <LogoMark />
        <span
          style={{
            fontFamily:    "'Outfit', 'Inter', system-ui, sans-serif",
            fontSize:      18,
            fontWeight:    700,
            letterSpacing: '-0.02em',
            color:         '#111318',
            lineHeight:    1,
          }}
        >
          Deal<span style={{ color: '#6E56CF' }}>Lens</span>
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-px">
        {NAV_ITEMS.map(({ to, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className="relative flex items-center pl-4 pr-3 py-2.5 rounded-xl text-sm transition-all duration-150"
            style={({ isActive }) => ({
              background: isActive ? 'rgba(110, 86, 207, 0.08)' : 'transparent',
              color:      isActive ? '#6E56CF' : '#667085',
              fontWeight: isActive ? 600 : 400,
            })}
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span
                    className="absolute left-0 top-1/2 -translate-y-1/2 rounded-full"
                    style={{ width: 2.5, height: 18, background: '#6E56CF' }}
                  />
                )}
                <span style={{ flex: 1 }}>{label}</span>
                {to === '/synergy' && pendingSynergy > 0 && (
                  <span style={{
                    background: '#6E56CF', color: '#fff',
                    borderRadius: 10, padding: '1px 6px',
                    fontSize: 10, fontWeight: 700, lineHeight: 1.6,
                    marginLeft: 4, flexShrink: 0,
                  }}>
                    {pendingSynergy}
                  </span>
                )}
                {to === '/monitor' && criticalCount > 0 && (
                  <span style={{
                    background: '#F04438', color: '#fff',
                    borderRadius: 10, padding: '1px 5px',
                    fontSize: 10, fontWeight: 700, lineHeight: 1.6,
                    marginLeft: 4, minWidth: 16, textAlign: 'center',
                    flexShrink: 0, display: 'inline-block',
                  }}>
                    {criticalCount}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div
        className="px-6 py-4 shrink-0"
        style={{ borderTop: '1px solid var(--border)' }}
      >
        <p
          style={{
            fontFamily:    "'JetBrains Mono', monospace",
            fontSize:      10,
            color:         'var(--tx-3)',
            letterSpacing: '0.10em',
            textTransform: 'uppercase',
          }}
        >
          CapAI Hack · Beta
        </p>
      </div>
    </aside>
  )
}

function Layout({ children, pendingSynergy, criticalCount }) {
  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)' }}>
      <Sidebar pendingSynergy={pendingSynergy} criticalCount={criticalCount} />
      <main style={{ marginLeft: 220, padding: '36px 44px', minHeight: '100vh' }}>
        {children}
      </main>
    </div>
  )
}

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0)
  const triggerRefresh = () => setRefreshKey(k => k + 1)
  const pendingSynergy = usePendingSynergy()
  const criticalCount = useCriticalAlerts()

  return (
    <BrowserRouter>
      <Layout pendingSynergy={pendingSynergy} criticalCount={criticalCount}>
        <Routes>
          <Route path="/"         element={<Dashboard refreshKey={refreshKey} />} />
          <Route path="/evaluate" element={<Evaluate onEvaluationComplete={triggerRefresh} />} />
          <Route path="/monitor"  element={<Monitor />} />
          <Route path="/synergy"  element={<Synergy />} />
          <Route path="/mandate"  element={<Mandate onApplied={triggerRefresh} />} />
          <Route path="/debug"    element={<Debug />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
