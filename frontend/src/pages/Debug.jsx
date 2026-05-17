import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Activity, GitBranch, Database, RefreshCw, Trash2, RotateCcw,
  Wifi, WifiOff, ChevronDown, ChevronRight, AlertCircle,
  CheckCircle, Clock, Loader,
} from 'lucide-react'

const API = 'http://localhost:8000/api'

// ── JSON Syntax Highlighting ─────────────────────────────────────────────────
// Returns React JSX elements with colored spans — no dangerouslySetInnerHTML.
function JsonHighlight({ value, depth }) {
  const d = depth ?? 0
  const pad = (n) => '  '.repeat(n)   // non-breaking spaces for indent

  if (value === null) return <span className="text-red-400">null</span>
  if (typeof value === 'boolean') return <span className="text-purple-400">{String(value)}</span>
  if (typeof value === 'number')  return <span className="text-blue-400">{value}</span>
  if (typeof value === 'string') {
    return (
      <>
        <span className="text-green-400">&quot;</span>
        <span className="text-green-300">{value}</span>
        <span className="text-green-400">&quot;</span>
      </>
    )
  }
  if (Array.isArray(value)) {
    if (!value.length) return <span className="text-slate-400">[]</span>
    return (
      <>
        <span className="text-slate-400">{'['}</span>{'\n'}
        {value.map((item, i) => (
          <span key={i}>
            {pad(d + 1)}
            <JsonHighlight value={item} depth={d + 1} />
            {i < value.length - 1 && <span className="text-slate-500">,</span>}
            {'\n'}
          </span>
        ))}
        {pad(d)}<span className="text-slate-400">{']'}</span>
      </>
    )
  }
  if (typeof value === 'object') {
    const entries = Object.entries(value)
    if (!entries.length) return <span className="text-slate-400">{'{}'}</span>
    return (
      <>
        <span className="text-slate-400">{'{'}</span>{'\n'}
        {entries.map(([k, v], i) => (
          <span key={k}>
            {pad(d + 1)}
            <span className="text-amber-300">&quot;{k}&quot;</span>
            <span className="text-slate-400">: </span>
            <JsonHighlight value={v} depth={d + 1} />
            {i < entries.length - 1 && <span className="text-slate-500">,</span>}
            {'\n'}
          </span>
        ))}
        {pad(d)}<span className="text-slate-400">{'}'}</span>
      </>
    )
  }
  return <span className="text-slate-300">{String(value)}</span>
}

// ── Log Level Styles ──────────────────────────────────────────────────────────
const LEVEL_STYLE = {
  DEBUG: 'text-slate-400',
  INFO:  'text-blue-400',
  WARN:  'text-amber-400',
  ERROR: 'text-red-400',
}

// ── Single Log Entry ──────────────────────────────────────────────────────────
function LogEntry({ log, expanded, onToggle }) {
  const ts = log.ts
    ? new Date(log.ts * 1000).toLocaleTimeString('en-US', {
        hour12: false,
        fractionalSecondDigits: 3,
      })
    : ''
  const hasDetail = log.detail && Object.keys(log.detail).length > 0

  return (
    <div className="border-b border-slate-800 hover:bg-slate-800/40 transition-colors">
      <div
        className={`flex items-center gap-3 px-4 py-2 font-mono text-xs ${hasDetail ? 'cursor-pointer' : 'cursor-default'}`}
        onClick={hasDetail ? onToggle : undefined}
      >
        {hasDetail ? (
          expanded
            ? <ChevronDown size={12} className="text-slate-500 shrink-0" />
            : <ChevronRight size={12} className="text-slate-500 shrink-0" />
        ) : (
          <span className="w-3 shrink-0" />
        )}
        <span className="text-slate-600 w-28 shrink-0">{ts}</span>
        <span className={`w-12 shrink-0 font-bold ${LEVEL_STYLE[log.level] ?? 'text-slate-300'}`}>
          {log.level}
        </span>
        <span className="text-indigo-400 w-32 shrink-0 truncate">{log.source}</span>
        <span className="text-slate-300 flex-1">{log.message}</span>
      </div>
      {expanded && hasDetail && (
        <div className="px-4 pb-3 ml-7">
          <pre className="text-xs bg-slate-900 rounded-md p-3 overflow-x-auto leading-5 whitespace-pre">
            <JsonHighlight value={log.detail} />
          </pre>
        </div>
      )}
    </div>
  )
}

// ── Pipeline Step Icon ────────────────────────────────────────────────────────
function StepIcon({ status }) {
  if (status === 'running') return <Loader size={13} className="animate-spin text-amber-400" />
  if (status === 'done')    return <CheckCircle size={13} className="text-green-400" />
  if (status === 'error')   return <AlertCircle size={13} className="text-red-400" />
  return <Clock size={13} className="text-slate-600" />
}

const STEP_ORDER  = ['extraction', 'business', 'esg', 'memory', 'aggregator', 'forecasting', 'fix_analysis', 'portfolio']
const STEP_LABEL  = {
  extraction:  'Extraction',
  business:    'Business',
  esg:         'ESG',
  memory:      'Memory',
  aggregator:  'Aggregator',
  forecasting: 'Forecasting',
  fix_analysis:'Fix Analysis',
  portfolio:   'Portfolio',
}

// ── Raw Text Collapsible ──────────────────────────────────────────────────────
function RawTextBlock({ text }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="bg-slate-800/40 rounded-lg">
      <button
        className="w-full flex items-center justify-between px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider hover:text-slate-200 transition-colors"
        onClick={() => setOpen(o => !o)}
      >
        <span>Extracted Raw Text ({text.length.toLocaleString()} chars)</span>
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      {open && (
        <pre className="px-4 pb-4 text-[11px] text-slate-400 leading-5 overflow-x-auto whitespace-pre-wrap max-h-72">
          {text}
        </pre>
      )}
    </div>
  )
}

// ── Pipeline Trace Tab ────────────────────────────────────────────────────────
function PipelineTab({ pipelineData }) {
  if (!pipelineData || !pipelineData.startup_name) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-500 text-sm">
        No pipeline data yet — run an evaluation to see the trace.
      </div>
    )
  }

  const steps       = pipelineData.steps        ?? {}
  const ollamaCalls = pipelineData.ollama_calls  ?? []
  const rawText     = pipelineData.raw_text      ?? ''

  return (
    <div className="space-y-5">
      {/* Run header */}
      <div className="bg-slate-800/60 rounded-lg p-4 flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-slate-200">{pipelineData.startup_name}</div>
          <div className="text-xs text-slate-500 mt-0.5 flex items-center gap-3">
            {pipelineData.active
              ? <span className="text-amber-400">● Running</span>
              : pipelineData.completed_at
                ? <span className="text-green-400">● Completed</span>
                : <span className="text-slate-600">● Idle</span>}
            {pipelineData.started_at && (
              <span className="text-slate-600">
                Started {new Date(pipelineData.started_at * 1000).toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Agent flow */}
      <div className="bg-slate-800/40 rounded-lg p-4">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Agent Flow</div>
        <div className="flex flex-wrap gap-3 items-center">
          {STEP_ORDER.map((key, idx) => {
            const step = steps[key] ?? {}
            const dur  = step.duration_ms != null ? `${step.duration_ms}ms` : null
            return (
              <div key={key} className="flex items-center gap-2">
                <div className={`bg-slate-900 border rounded-lg px-3 py-2 min-w-[110px] ${
                  step.status === 'done'    ? 'border-green-500/40' :
                  step.status === 'running' ? 'border-amber-500/60 shadow-amber-900/30 shadow-md' :
                  step.status === 'error'   ? 'border-red-500/40' :
                  'border-slate-700'
                }`}>
                  <div className="flex items-center gap-1.5 mb-1">
                    <StepIcon status={step.status} />
                    <span className="text-xs font-medium text-slate-200">{STEP_LABEL[key]}</span>
                  </div>
                  {dur && <div className="text-[10px] text-slate-500">{dur}</div>}
                  {step.result_summary && (
                    <div className="text-[10px] text-slate-400 mt-0.5 leading-tight">{step.result_summary}</div>
                  )}
                  {step.error && (
                    <div className="text-[10px] text-red-400 mt-0.5 leading-tight">
                      {step.error_type}: {step.error}
                    </div>
                  )}
                </div>
                {idx < STEP_ORDER.length - 1 && (
                  <span className="text-slate-600 text-sm select-none">→</span>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Ollama call table */}
      {ollamaCalls.length > 0 && (
        <div className="bg-slate-800/40 rounded-lg p-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Ollama Calls ({ollamaCalls.length})
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono">
              <thead>
                <tr className="text-slate-500 border-b border-slate-700">
                  <th className="text-left pb-2 pr-4 font-normal">Agent</th>
                  <th className="text-left pb-2 pr-4 font-normal">Model</th>
                  <th className="text-left pb-2 pr-4 font-normal">Duration</th>
                  <th className="text-left pb-2 pr-4 font-normal">Parse</th>
                  <th className="text-left pb-2 font-normal">Response preview</th>
                </tr>
              </thead>
              <tbody>
                {ollamaCalls.map((call, i) => (
                  <tr key={i} className="border-b border-slate-800 hover:bg-slate-800/40">
                    <td className="py-2 pr-4 text-indigo-400">{call.agent}</td>
                    <td className="py-2 pr-4 text-slate-300">{call.model}</td>
                    <td className="py-2 pr-4 text-slate-400">{call.duration_ms}ms</td>
                    <td className="py-2 pr-4">
                      {call.parse_success
                        ? <span className="text-green-400">✓ OK</span>
                        : <span className="text-red-400">✗ FAIL</span>}
                    </td>
                    <td className="py-2 text-slate-500 max-w-[240px] truncate">{call.response_preview}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {rawText && <RawTextBlock text={rawText} />}
    </div>
  )
}

// ── Knowledge Graph Tab ───────────────────────────────────────────────────────
// DB table nodes with live record counts from the API
const DB_NODES = [
  { id: 'deal_history',        label: 'deal_history',        color: '#6366f1' },
  { id: 'entity_sectors',      label: 'entity_sectors',      color: '#22c55e' },
  { id: 'portfolio_companies', label: 'portfolio_companies',  color: '#f59e0b' },
  { id: 'esg_red_flags',       label: 'esg_red_flags',       color: '#ef4444' },
  { id: 'entity_founders',     label: 'entity_founders',     color: '#a78bfa' },
  { id: 'cached_evaluations',  label: 'cached_evaluations',  color: '#38bdf8' },
]

function GraphTab({ graphData, onRefreshGraph }) {
  const [selectedNode, setSelectedNode] = useState(null)

  const getCount = (tableId) => {
    if (!graphData) return '–'
    const t = graphData.tables?.[tableId]
    return t != null ? t.count.toLocaleString() : '0'
  }

  const getSample = (tableId) => {
    if (!graphData) return []
    return graphData.tables?.[tableId]?.sample ?? []
  }

  const selected = selectedNode ? DB_NODES.find(n => n.id === selectedNode) : null
  const sample   = selectedNode ? getSample(selectedNode) : []

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">
          Live record counts · click a stat card to inspect rows · hover nodes in the graph to explore relationships
        </p>
        <button
          onClick={onRefreshGraph}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
        >
          <RefreshCw size={12} /> Refresh
        </button>
      </div>

      {/* Stat cards — DB tables only */}
      <div className="grid grid-cols-3 gap-3">
        {DB_NODES.map(n => (
          <button
            key={n.id}
            onClick={() => setSelectedNode(selectedNode === n.id ? null : n.id)}
            className={`text-left bg-slate-800/60 rounded-lg p-3 flex items-center gap-3 border transition-colors ${
              selectedNode === n.id ? 'border-indigo-500/60' : 'border-transparent hover:border-slate-600'
            }`}
          >
            <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: n.color }} />
            <div className="flex-1 min-w-0">
              <div className="text-xs font-mono text-slate-400 truncate">{n.label}</div>
              <div className="text-xl font-bold text-slate-100 leading-tight">{getCount(n.id)}</div>
              <div className="text-[10px] text-slate-600">records</div>
            </div>
          </button>
        ))}
      </div>

      {/* Row inspector */}
      {selected && (
        <div className="bg-slate-800/60 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: selected.color }} />
            <span className="text-sm font-mono font-semibold text-slate-200">{selected.label}</span>
            <span className="text-xs text-slate-500">— {getCount(selected.id)} records (showing up to 5)</span>
          </div>
          {sample.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-[11px] font-mono">
                <thead>
                  <tr className="text-slate-500 border-b border-slate-700">
                    {Object.keys(sample[0]).map(k => (
                      <th key={k} className="text-left pb-2 pr-4 font-normal">{k}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sample.map((row, i) => (
                    <tr key={i} className="border-b border-slate-800">
                      {Object.values(row).map((v, j) => (
                        <td key={j} className="py-1.5 pr-4 text-slate-300 max-w-[160px] truncate">
                          {v === null ? <span className="text-slate-600">null</span> : String(v)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-slate-500">No records found.</p>
          )}
        </div>
      )}

      {/* D3 force-directed architecture graph */}
      <div className="rounded-lg overflow-hidden border border-slate-800" style={{ height: '520px' }}>
        <iframe
          src="/knowledge-graph.html"
          title="ConvictAI Memory Architecture"
          className="w-full h-full border-0"
          style={{ background: '#0f172a' }}
        />
      </div>
    </div>
  )
}

// ── Status Bar ────────────────────────────────────────────────────────────────
function StatusBar({
  ollamaOnline, graphData, pipelineData,
  onClearLogs, onReseed, onReset,
  showResetConfirm, setShowResetConfirm,
}) {
  const totalRecords = graphData?.tables
    ? Object.values(graphData.tables).reduce((s, t) => s + (t.count ?? 0), 0)
    : '–'
  const dbPath       = graphData?.db_path ?? 'convictai.db'

  return (
    <div className="sticky top-14 z-40 bg-slate-900/95 border-b border-slate-700 backdrop-blur-sm">
      <div className="flex items-center gap-5 px-6 py-2.5 flex-wrap">
        <div className="flex items-center gap-1.5 text-xs">
          {ollamaOnline
            ? <Wifi size={13} className="text-green-400" />
            : <WifiOff size={13} className="text-red-400" />}
          <span className={ollamaOnline ? 'text-green-400' : 'text-red-400'}>
            Ollama {ollamaOnline ? 'online' : 'offline'}
          </span>
        </div>

        <div className="w-px h-4 bg-slate-700" />

        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <Database size={12} />
          <span className="font-mono">{dbPath}</span>
          <span className="text-slate-600">·</span>
          <span>{totalRecords} rows total</span>
        </div>

        <div className="w-px h-4 bg-slate-700" />

        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <Activity size={12} />
          {pipelineData?.active
            ? <span className="text-amber-400">Evaluating: {pipelineData.startup_name}</span>
            : <span>Idle</span>}
        </div>

        <div className="flex-1" />

        <button
          onClick={onClearLogs}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 px-2.5 py-1.5 rounded hover:bg-slate-800 transition-colors"
        >
          <Trash2 size={12} /> Clear Logs
        </button>

        <button
          onClick={onReseed}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-amber-300 px-2.5 py-1.5 rounded hover:bg-slate-800 transition-colors"
        >
          <RefreshCw size={12} /> Re-seed DB
        </button>

        {showResetConfirm ? (
          <div className="flex items-center gap-2">
            <span className="text-xs text-red-400 font-medium">Drop all tables?</span>
            <button
              onClick={onReset}
              className="text-xs bg-red-600 hover:bg-red-500 text-white px-2.5 py-1 rounded transition-colors"
            >
              Confirm
            </button>
            <button
              onClick={() => setShowResetConfirm(false)}
              className="text-xs text-slate-400 hover:text-slate-200 px-2 py-1"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowResetConfirm(true)}
            className="flex items-center gap-1.5 text-xs text-red-500 hover:text-red-400 px-2.5 py-1.5 rounded hover:bg-slate-800 transition-colors"
          >
            <RotateCcw size={12} /> Reset DB
          </button>
        )}
      </div>
    </div>
  )
}

// ── Main Debug Page ───────────────────────────────────────────────────────────
export default function Debug() {
  const [activeTab, setActiveTab]           = useState('logs')
  const [logs, setLogs]                     = useState([])
  const [expandedLogs, setExpandedLogs]     = useState({})
  const [logFilter, setLogFilter]           = useState('')
  const [levelFilter, setLevelFilter]       = useState('ALL')
  const [pipelineData, setPipelineData]     = useState(null)
  const [graphData, setGraphData]           = useState(null)
  const [ollamaOnline, setOllamaOnline]     = useState(false)
  const [showResetConfirm, setShowResetConfirm] = useState(false)
  const [toast, setToast]                   = useState(null)

  const logsEndRef      = useRef(null)
  const autoScrollRef   = useRef(true)
  const logContainerRef = useRef(null)

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  // Ollama health poll
  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch(`${API}/health`)
        const d = await r.json()
        setOllamaOnline(d.ollama === true)
      } catch {
        setOllamaOnline(false)
      }
    }
    check()
    const id = setInterval(check, 10000)
    return () => clearInterval(id)
  }, [])

  // SSE — live logs (always connected; display:none keeps socket alive across tabs)
  useEffect(() => {
    let es
    const connect = () => {
      es = new EventSource(`${API}/debug/logs/stream`)
      es.onmessage = (e) => {
        try { setLogs(prev => [...prev, JSON.parse(e.data)]) } catch {}
      }
      es.onerror = () => { es.close(); setTimeout(connect, 3000) }
    }
    connect()
    return () => es?.close()
  }, [])

  // SSE — pipeline state
  useEffect(() => {
    let es
    const connect = () => {
      es = new EventSource(`${API}/debug/pipeline/stream`)
      es.onmessage = (e) => {
        try { setPipelineData(JSON.parse(e.data)) } catch {}
      }
      es.onerror = () => { es.close(); setTimeout(connect, 3000) }
    }
    connect()
    return () => es?.close()
  }, [])

  // Graph data
  const loadGraph = useCallback(async () => {
    try {
      const r = await fetch(`${API}/debug/graph`)
      setGraphData(await r.json())
    } catch {}
  }, [])

  useEffect(() => { loadGraph() }, [loadGraph])

  // Auto-scroll
  useEffect(() => {
    if (autoScrollRef.current) logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const handleScroll = () => {
    const el = logContainerRef.current
    if (el) autoScrollRef.current = el.scrollTop + el.clientHeight >= el.scrollHeight - 20
  }

  const toggleExpand = (idx) => setExpandedLogs(prev => ({ ...prev, [idx]: !prev[idx] }))

  const clearLogs = async () => {
    await fetch(`${API}/debug/logs`, { method: 'DELETE' })
    setLogs([])
    showToast('Logs cleared')
  }

  const reseedDb = async () => {
    await fetch(`${API}/debug/db/reseed`, { method: 'POST' })
    await loadGraph()
    showToast('Database re-seeded', 'success')
  }

  const resetDb = async () => {
    await fetch(`${API}/debug/db/reset`, { method: 'POST' })
    setLogs([])
    await loadGraph()
    setShowResetConfirm(false)
    showToast('Database reset complete', 'success')
  }

  const LEVEL_OPTS = ['ALL', 'DEBUG', 'INFO', 'WARN', 'ERROR']

  const filteredLogs = logs.filter(l => {
    const okLevel = levelFilter === 'ALL' || l.level === levelFilter
    const okText  = !logFilter ||
      l.message?.toLowerCase().includes(logFilter.toLowerCase()) ||
      l.source?.toLowerCase().includes(logFilter.toLowerCase())
    return okLevel && okText
  })

  const tabs = [
    { id: 'logs',     label: 'Live Logs',       icon: <Activity size={14} /> },
    { id: 'pipeline', label: 'Pipeline Trace',   icon: <GitBranch size={14} /> },
    { id: 'graph',    label: 'Knowledge Graph',  icon: <Database size={14} /> },
  ]

  return (
    <div className="-mx-6 -mt-8">
      <StatusBar
        ollamaOnline={ollamaOnline}
        graphData={graphData}
        pipelineData={pipelineData}
        onClearLogs={clearLogs}
        onReseed={reseedDb}
        onReset={resetDb}
        showResetConfirm={showResetConfirm}
        setShowResetConfirm={setShowResetConfirm}
      />

      {/* Tab bar */}
      <div className="border-b border-slate-700 bg-slate-900/80 px-6">
        <div className="flex">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === t.id
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              {t.icon}{t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-lg text-sm shadow-xl ${
          toast.type === 'success' ? 'bg-green-600 text-white' : 'bg-slate-700 text-slate-200'
        }`}>
          {toast.msg}
        </div>
      )}

      {/* ── Logs tab — display:none to keep EventSource alive ── */}
      <div className="p-6" style={{ display: activeTab === 'logs' ? 'block' : 'none' }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="flex gap-1">
            {LEVEL_OPTS.map(lv => (
              <button
                key={lv}
                onClick={() => setLevelFilter(lv)}
                className={`text-xs px-2.5 py-1 rounded font-mono transition-colors ${
                  levelFilter === lv
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {lv}
              </button>
            ))}
          </div>
          <input
            value={logFilter}
            onChange={e => setLogFilter(e.target.value)}
            placeholder="Filter by message or source…"
            className="flex-1 bg-slate-800 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          <span className="text-xs text-slate-600 shrink-0">{filteredLogs.length} entries</span>
        </div>

        <div
          ref={logContainerRef}
          onScroll={handleScroll}
          className="bg-slate-900 rounded-lg overflow-auto border border-slate-800"
          style={{ height: 'calc(100vh - 290px)' }}
        >
          {filteredLogs.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-slate-600 text-sm">
              No logs yet — run an evaluation to see output here
            </div>
          ) : (
            filteredLogs.map((log, idx) => (
              <LogEntry
                key={idx}
                log={log}
                expanded={!!expandedLogs[idx]}
                onToggle={() => toggleExpand(idx)}
              />
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </div>

      {/* ── Pipeline tab ── */}
      <div className="p-6" style={{ display: activeTab === 'pipeline' ? 'block' : 'none' }}>
        <PipelineTab pipelineData={pipelineData} />
      </div>

      {/* ── Graph tab ── */}
      <div className="p-6" style={{ display: activeTab === 'graph' ? 'block' : 'none' }}>
        <GraphTab graphData={graphData} onRefreshGraph={loadGraph} />
      </div>
    </div>
  )
}
