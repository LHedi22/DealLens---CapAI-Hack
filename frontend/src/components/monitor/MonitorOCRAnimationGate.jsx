import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getMonitorOcrMock, confirmMonitorOcr } from '../../lib/api'

// ── Shared primitives (identical pattern to OCRAnimationGate) ─────────────────

const QUALITY_ITEMS = [
  'PDF format detected ✓',
  'Resolution acceptable ✓',
  'Language: French / Arabic ✓',
  'Table structure identified ✓',
]

const CATEGORIES = [
  'rd', 'construction', 'equipment', 'salaries',
  'working_capital', 'marketing', 'training', 'other',
]

const CAT_STYLE = {
  rd:             'bg-indigo-900/50 text-indigo-300 border-indigo-700',
  construction:   'bg-yellow-900/50 text-yellow-300 border-yellow-700',
  equipment:      'bg-blue-900/50 text-blue-300 border-blue-700',
  salaries:       'bg-green-900/50 text-green-300 border-green-700',
  working_capital:'bg-teal-900/50 text-teal-300 border-teal-700',
  marketing:      'bg-pink-900/50 text-pink-300 border-pink-700',
  training:       'bg-purple-900/50 text-purple-300 border-purple-700',
  other:          'bg-slate-800 text-slate-400 border-slate-600',
}

function fmt(n) {
  return Number(n).toLocaleString('fr-TN', { minimumFractionDigits: 3 })
}

function ProgressBar({ durationMs }) {
  return (
    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
      <motion.div
        className="h-full bg-indigo-500 rounded-full"
        initial={{ width: '0%' }}
        animate={{ width: '100%' }}
        transition={{ duration: durationMs / 1000, ease: 'linear' }}
      />
    </div>
  )
}

function FadeLine({ children, delay = 0, className = '' }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -4 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay, duration: 0.22 }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

function StepHeader({ title, subtitle }) {
  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 mb-1">
        <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping" />
        <h2 className="text-slate-100 font-semibold text-lg">{title}</h2>
      </div>
      {subtitle && <p className="text-slate-500 text-sm pl-4">{subtitle}</p>}
    </div>
  )
}

// ── Step 1 — Quality check ────────────────────────────────────────────────────

function Step1Quality({ onDone }) {
  const [shown, setShown] = useState([])

  useEffect(() => {
    const timers = []
    QUALITY_ITEMS.forEach((_, i) => {
      timers.push(setTimeout(() => setShown(p => [...p, i]), 600 + i * 350))
    })
    timers.push(setTimeout(onDone, 600 + QUALITY_ITEMS.length * 350 + 200))
    return () => timers.forEach(clearTimeout)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-4">
      <StepHeader title="Reading document quality..." />
      <ProgressBar durationMs={1500} />
      <div className="space-y-1.5 pt-2">
        {QUALITY_ITEMS.map((item, i) =>
          shown.includes(i) ? (
            <FadeLine key={i} className="text-sm text-green-400 font-mono">{item}</FadeLine>
          ) : null
        )}
      </div>
    </div>
  )
}

// ── Step 2 — Row identification ───────────────────────────────────────────────

function Step2Rows({ transactions, onDone }) {
  const [shown, setShown] = useState([])

  useEffect(() => {
    const timers = []
    transactions.forEach((_, i) => {
      timers.push(setTimeout(() => setShown(p => [...p, i]), i * 230))
    })
    timers.push(setTimeout(onDone, transactions.length * 230 + 350))
    return () => timers.forEach(clearTimeout)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-4">
      <StepHeader title="Identifying transaction rows..." subtitle={`${transactions.length} rows detected`} />
      <div className="bg-slate-900 rounded-lg border border-slate-700 p-3 space-y-1 min-h-[180px] font-mono text-xs">
        {transactions.map((tx, i) =>
          shown.includes(i) ? (
            <FadeLine key={i} className="text-slate-400">
              <span className="text-slate-600">{tx.transaction_date?.slice(5)}</span>
              {' → '}
              <span className="text-slate-300">{tx.beneficiary}</span>
            </FadeLine>
          ) : null
        )}
      </div>
    </div>
  )
}

// ── Step 3 — Amount extraction ────────────────────────────────────────────────

function Step3Amounts({ transactions, onDone }) {
  const [shown, setShown] = useState([])

  useEffect(() => {
    const timers = []
    transactions.forEach((_, i) => {
      timers.push(setTimeout(() => setShown(p => [...p, i]), i * 200))
    })
    timers.push(setTimeout(onDone, transactions.length * 200 + 350))
    return () => timers.forEach(clearTimeout)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-4">
      <StepHeader title="Extracting amounts and beneficiaries..." />
      <div className="bg-slate-900 rounded-lg border border-slate-700 p-3 space-y-1 min-h-[180px] font-mono text-xs">
        {transactions.map((tx, i) => (
          <div key={i} className="flex justify-between gap-4">
            <span className="text-slate-500">{tx.transaction_date?.slice(5)}</span>
            <span className="text-slate-300 flex-1 truncate">{tx.beneficiary}</span>
            {shown.includes(i) ? (
              <FadeLine className="text-white font-semibold tabular-nums shrink-0">
                {fmt(tx.amount_tnd)} TND
              </FadeLine>
            ) : (
              <span className="text-slate-700 tabular-nums shrink-0">···</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Step 4 — AI classification ────────────────────────────────────────────────

function Step4Classification({ transactions, onDone }) {
  const [shown, setShown] = useState([])

  useEffect(() => {
    const timers = []
    transactions.forEach((_, i) => {
      timers.push(setTimeout(() => setShown(p => [...p, i]), i * 200))
    })
    timers.push(setTimeout(onDone, transactions.length * 200 + 400))
    return () => timers.forEach(clearTimeout)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-4">
      <StepHeader title="Classifying transactions..." subtitle="Matching against SICAR agreement categories" />
      <div className="space-y-1">
        {transactions.map((tx, i) => {
          const isUnclassified = tx.classification_status === 'UNCLASSIFIED'
          return (
            <div
              key={i}
              className="flex items-center justify-between bg-slate-800/50 rounded px-3 py-1.5 gap-3"
            >
              <span className="text-slate-400 text-xs font-mono shrink-0">{tx.transaction_date?.slice(5)}</span>
              <span className="text-slate-300 text-xs flex-1 truncate">{tx.beneficiary}</span>
              {shown.includes(i) ? (
                <FadeLine>
                  {isUnclassified ? (
                    <span className="text-xs px-2 py-0.5 rounded border font-semibold bg-red-900/50 text-red-300 border-red-700">
                      UNCLASSIFIED
                    </span>
                  ) : (
                    <span className={`text-xs px-2 py-0.5 rounded border font-semibold ${CAT_STYLE[tx.ai_category] ?? CAT_STYLE.other}`}>
                      {(tx.ai_category ?? 'other').replace(/_/g, ' ')}
                    </span>
                  )}
                </FadeLine>
              ) : (
                <span className="text-xs text-slate-700">···</span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Step 5 — PE review gate ───────────────────────────────────────────────────

function Step5ReviewGate({ mockData, startupName, onResult }) {
  const [txs, setTxs] = useState(
    (mockData?.review_transactions ?? []).map(t => ({ ...t, human_category: null }))
  )
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState(null)

  function setCategory(idx, cat) {
    setTxs(prev => prev.map((t, i) =>
      i === idx
        ? { ...t, human_category: cat, classification_status: 'HUMAN_VERIFIED' }
        : t
    ))
  }

  const stillUnclassified = txs.filter(
    t => t.classification_status === 'UNCLASSIFIED' && !t.human_category
  )

  async function handleConfirm() {
    setConfirming(true)
    setError(null)
    try {
      const result = await confirmMonitorOcr({
        startup_name: startupName,
        statement_month: mockData.statement_month,
        confirmed_transactions: txs.map(t => ({
          transaction_date: t.transaction_date,
          beneficiary: t.beneficiary,
          amount_tnd: t.amount_tnd,
          memo: t.memo,
          human_category: t.human_category || null,
        })),
      })
      onResult(result)
    } catch (e) {
      setError(e.message || 'Import failed.')
      setConfirming(false)
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-slate-100 font-semibold text-lg">Review classified transactions</h2>
        <p className="text-slate-400 text-sm mt-1">
          Verify AI classifications before importing to the compliance ledger.
          {stillUnclassified.length > 0 && (
            <span className="ml-2 text-red-400">
              {stillUnclassified.length} transaction{stillUnclassified.length > 1 ? 's require' : ' requires'} manual classification.
            </span>
          )}
        </p>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-700">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-700 bg-slate-800/60">
              <th className="text-left py-2 px-3 text-slate-400 font-medium">Date</th>
              <th className="text-left py-2 px-3 text-slate-400 font-medium">Beneficiary</th>
              <th className="text-right py-2 px-3 text-slate-400 font-medium">Amount (TND)</th>
              <th className="text-left py-2 px-3 text-slate-400 font-medium">Category</th>
            </tr>
          </thead>
          <tbody>
            {txs.map((t, i) => {
              const effectiveCat = t.human_category || t.ai_category
              const isUnclassified = t.classification_status === 'UNCLASSIFIED' && !t.human_category
              return (
                <motion.tr
                  key={i}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.04 }}
                  className={`border-b border-slate-800 last:border-0 ${
                    isUnclassified ? 'bg-red-950/25' : ''
                  }`}
                >
                  <td className="py-2 px-3 text-slate-400 font-mono">{t.transaction_date?.slice(5)}</td>
                  <td className="py-2 px-3 text-slate-200 max-w-[200px] truncate">
                    {t.beneficiary}
                    {isUnclassified && (
                      <span className="ml-2 text-red-400 text-[10px]">↑ review required</span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-right text-white font-medium tabular-nums">
                    {fmt(t.amount_tnd)}
                  </td>
                  <td className="py-2 px-3">
                    <select
                      value={effectiveCat || ''}
                      onChange={e => setCategory(i, e.target.value)}
                      className={`text-xs rounded px-2 py-1 border font-semibold cursor-pointer focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors ${
                        isUnclassified
                          ? 'border-red-600 text-red-300 bg-red-950/60'
                          : `${CAT_STYLE[effectiveCat] ?? CAT_STYLE.other}`
                      }`}
                    >
                      {isUnclassified && (
                        <option value="" disabled>— select —</option>
                      )}
                      {CATEGORIES.map(c => (
                        <option key={c} value={c} className="bg-slate-900 text-slate-100">
                          {c.replace(/_/g, ' ')}
                        </option>
                      ))}
                    </select>
                  </td>
                </motion.tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {error && (
        <p className="text-red-400 text-xs">{error}</p>
      )}

      <motion.button
        onClick={handleConfirm}
        disabled={confirming}
        whileHover={{ scale: confirming ? 1 : 1.01 }}
        whileTap={{ scale: confirming ? 1 : 0.99 }}
        className="w-full py-3 rounded-xl bg-green-600 hover:bg-green-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold text-base transition-colors mt-2"
      >
        {confirming
          ? 'Importing to compliance ledger...'
          : `Confirm and Import ${txs.length} Transactions →`}
      </motion.button>

      {stillUnclassified.length > 0 && !confirming && (
        <p className="text-slate-500 text-xs text-center">
          You can still confirm with unclassified items — they will appear in the Transactions tab for review.
        </p>
      )}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

const STEP_LABELS = ['Quality', 'Rows', 'Amounts', 'Classify', 'Review']

export default function MonitorOCRAnimationGate({ startupName, fileName, onResult }) {
  const [step, setStep] = useState(1)
  const [mockData, setMockData] = useState(null)
  const [fetchError, setFetchError] = useState(false)

  // Pre-fetch mock data immediately so it's ready for steps 2+
  useEffect(() => {
    getMonitorOcrMock()
      .then(data => setMockData(data))
      .catch(() => setFetchError(true))
  }, [])

  if (fetchError) {
    return (
      <div className="bg-red-950/40 border border-red-700 rounded-xl p-6 text-center">
        <p className="text-red-300 font-medium">Could not load bank statement mock data.</p>
        <p className="text-red-500 text-sm mt-1">Ensure the backend is running at localhost:8000.</p>
      </div>
    )
  }

  return (
    <div className="bg-[#1e293b] border border-slate-700 rounded-xl p-6 space-y-6">
      {/* Step indicator */}
      <div className="flex items-center gap-2">
        {STEP_LABELS.map((label, i) => {
          const num = i + 1
          const done   = num < step
          const active = num === step
          return (
            <div key={num} className="flex items-center gap-2">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 transition-colors ${
                done   ? 'bg-green-600 text-white' :
                active ? 'bg-indigo-600 text-white' :
                         'bg-slate-700 text-slate-500'
              }`}>
                {done ? '✓' : num}
              </div>
              {num < STEP_LABELS.length && (
                <div className={`h-px w-5 transition-colors ${done ? 'bg-green-600' : 'bg-slate-700'}`} />
              )}
            </div>
          )
        })}
        {fileName && (
          <span className="ml-3 text-xs text-slate-500 truncate">· {fileName}</span>
        )}
      </div>

      {/* Step content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.22 }}
        >
          {step === 1 && (
            <Step1Quality onDone={() => setStep(2)} />
          )}

          {step === 2 && !mockData && (
            <div className="flex items-center gap-3 py-8">
              <div className="w-2 h-2 bg-indigo-400 rounded-full animate-ping" />
              <span className="text-slate-400 text-sm">Loading statement data...</span>
            </div>
          )}
          {step === 2 && mockData && (
            <Step2Rows
              transactions={mockData.review_transactions}
              onDone={() => setStep(3)}
            />
          )}

          {step === 3 && mockData && (
            <Step3Amounts
              transactions={mockData.review_transactions}
              onDone={() => setStep(4)}
            />
          )}

          {step === 4 && mockData && (
            <Step4Classification
              transactions={mockData.review_transactions}
              onDone={() => setStep(5)}
            />
          )}

          {step === 5 && mockData && (
            <Step5ReviewGate
              mockData={mockData}
              startupName={startupName}
              onResult={onResult}
            />
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
