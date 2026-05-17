import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getOcrMock, confirmOcr } from '../../lib/api'

const QUALITY_CHECKS = [
  'Resolution ✓',
  'Clarity ✓',
  'Skew correction ✓',
  'Lighting ✓',
]

const PREPROCESSING_STEPS = [
  '→ Deskewing document',
  '→ Binarizing (colour → black & white)',
  '→ Removing noise',
  '→ Normalising to 300 DPI',
]

const OCR_LINES = [
  'EduTech Tunisia — Pre-Seed Investment Proposal',
  'Founders: Amira Belhaj (CEO), Karim Mansour (CTO)',
  'Market: $2.4B MENA EdTech — 28% CAGR (RedSeer 2023)',
  'Revenue model: B2B SaaS — school licenses + seat fees',
  'ARR: $18,000 · Pilots: 3 schools · Students: 1,400',
  'Funding ask: $400,000 pre-seed',
  'Competitors: Edraak, Noon Academy, Google Classroom',
  'Differentiation: Arabic-first, Tunisian national syllabus',
  '[UNCLEAR] — handwritten note, line 4',
  'Governance: [UNCLEAR] board structure not stated',
]

const STRUCTURE_SECTIONS = [
  { label: 'Team',            confidence: 'HIGH'   },
  { label: 'Market',          confidence: 'HIGH'   },
  { label: 'Revenue Model',   confidence: 'MEDIUM' },
  { label: 'Traction',        confidence: 'HIGH'   },
  { label: 'Financials',      confidence: 'MEDIUM' },
  { label: 'ESG / Governance',confidence: 'LOW'    },
  { label: 'Competition',     confidence: 'HIGH'   },
]

const CONFIDENCE_COLORS = {
  HIGH:   'text-green-400 bg-green-900/40 border-green-700',
  MEDIUM: 'text-yellow-400 bg-yellow-900/40 border-yellow-700',
  LOW:    'text-red-400 bg-red-900/40 border-red-700',
}

const SOURCE_LABELS = {
  PRINTED:                 { label: 'Printed',   color: 'text-slate-400' },
  MIXED:                   { label: 'Mixed',     color: 'text-yellow-400' },
  HANDWRITTEN_UNVERIFIED:  { label: 'Handwritten — verify carefully', color: 'text-red-400' },
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
      transition={{ delay, duration: 0.25 }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

function StepHeader({ title, subtitle }) {
  return (
    <div className="mb-5">
      <div className="flex items-center gap-2 mb-1">
        <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping" />
        <h2 className="text-slate-100 font-semibold text-lg">{title}</h2>
      </div>
      {subtitle && <p className="text-slate-500 text-sm pl-4">{subtitle}</p>}
    </div>
  )
}

// ── Step 1 ────────────────────────────────────────────────────────────────────
function Step1QualityCheck({ onDone }) {
  const [shown, setShown] = useState([])

  useEffect(() => {
    // Start progress bar, then show checks 350ms apart, then advance
    const timers = []
    QUALITY_CHECKS.forEach((_, i) => {
      timers.push(setTimeout(() => setShown(prev => [...prev, i]), 600 + i * 350))
    })
    timers.push(setTimeout(onDone, 600 + QUALITY_CHECKS.length * 350 + 200))
    return () => timers.forEach(clearTimeout)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-4">
      <StepHeader title="Checking document quality..." />
      <ProgressBar durationMs={1500} />
      <div className="space-y-1.5 pt-2">
        {QUALITY_CHECKS.map((check, i) =>
          shown.includes(i) ? (
            <FadeLine key={i} delay={0} className="text-sm text-green-400 font-mono">
              {check}
            </FadeLine>
          ) : null
        )}
      </div>
    </div>
  )
}

// ── Step 2 ────────────────────────────────────────────────────────────────────
function Step2Preprocessing({ onDone }) {
  const [shown, setShown] = useState([])

  useEffect(() => {
    const timers = []
    PREPROCESSING_STEPS.forEach((_, i) => {
      timers.push(setTimeout(() => setShown(prev => [...prev, i]), i * 450))
    })
    timers.push(setTimeout(onDone, PREPROCESSING_STEPS.length * 450 + 300))
    return () => timers.forEach(clearTimeout)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-4">
      <StepHeader title="Pre-processing image..." />
      <div className="space-y-2">
        {PREPROCESSING_STEPS.map((step, i) =>
          shown.includes(i) ? (
            <FadeLine key={i} delay={0} className="text-sm text-slate-300 font-mono">
              {step}
            </FadeLine>
          ) : null
        )}
      </div>
    </div>
  )
}

// ── Step 3 ────────────────────────────────────────────────────────────────────
function Step3Scanning({ onDone }) {
  const [shown, setShown] = useState([])
  const [blink, setBlink] = useState(true)

  useEffect(() => {
    const timers = []
    OCR_LINES.forEach((_, i) => {
      timers.push(setTimeout(() => setShown(prev => [...prev, i]), i * 300))
    })
    timers.push(setTimeout(onDone, OCR_LINES.length * 300 + 400))
    return () => timers.forEach(clearTimeout)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const id = setInterval(() => setBlink(b => !b), 500)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="space-y-4">
      <StepHeader title="Reading document..." subtitle="Extracting text line by line" />
      <div className="bg-slate-900 rounded-lg p-4 font-mono text-xs space-y-1 min-h-[200px] border border-slate-700">
        {OCR_LINES.map((line, i) => {
          if (!shown.includes(i)) return null
          const isUnclear = line.includes('[UNCLEAR]')
          return (
            <FadeLine key={i} delay={0} className={isUnclear ? 'text-amber-400' : 'text-slate-300'}>
              {line}
            </FadeLine>
          )
        })}
        {shown.length > 0 && shown.length < OCR_LINES.length && (
          <span className={`text-indigo-400 ${blink ? 'opacity-100' : 'opacity-0'}`}>|</span>
        )}
      </div>
    </div>
  )
}

// ── Step 4 ────────────────────────────────────────────────────────────────────
function Step4Structure({ onDone }) {
  const [shown, setShown] = useState([])

  useEffect(() => {
    const timers = []
    STRUCTURE_SECTIONS.forEach((_, i) => {
      timers.push(setTimeout(() => setShown(prev => [...prev, i]), i * 250))
    })
    timers.push(setTimeout(onDone, STRUCTURE_SECTIONS.length * 250 + 300))
    return () => timers.forEach(clearTimeout)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-4">
      <StepHeader title="Structuring document..." subtitle="Mapping content to investment schema" />
      <div className="space-y-2">
        {STRUCTURE_SECTIONS.map((sec, i) =>
          shown.includes(i) ? (
            <FadeLine key={i} delay={0}>
              <div className="flex items-center justify-between bg-slate-800 rounded-lg px-4 py-2.5 border border-slate-700">
                <span className="text-slate-200 text-sm font-medium">{sec.label}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${CONFIDENCE_COLORS[sec.confidence]}`}>
                  {sec.confidence}
                </span>
              </div>
            </FadeLine>
          ) : null
        )}
      </div>
    </div>
  )
}

// ── Step 5 — Investor Review Gate ────────────────────────────────────────────
function Step5ReviewGate({ onConfirm }) {
  const [ocrData, setOcrData] = useState(null)
  const [sectionValues, setSectionValues] = useState({})
  const [extraNote, setExtraNote] = useState('')
  const [confirming, setConfirming] = useState(false)
  const originalValues = useRef({})

  useEffect(() => {
    getOcrMock().then(data => {
      setOcrData(data)
      const initial = {}
      data.review_sections.forEach(s => {
        initial[s.section_name] = s.content
      })
      setSectionValues(initial)
      originalValues.current = { ...initial }
    }).catch(() => {
      // If API fails, use stub data so review gate still renders
      const stub = {
        parsed_document: {},
        review_sections: [],
        parsing_metadata: { ocr_confidence: 0.71, visual_content_flagged: [] },
      }
      setOcrData(stub)
    })
  }, [])

  async function handleConfirm() {
    if (!ocrData) return
    setConfirming(true)

    const corrections = Object.entries(sectionValues)
      .filter(([name, val]) => val !== originalValues.current[name])
      .map(([section_name, corrected_value]) => ({
        section_name,
        original_value: originalValues.current[section_name] || '',
        corrected_value,
      }))

    try {
      const result = await confirmOcr({
        confirmed_document: ocrData.parsed_document,
        corrections,
        sector: 'EdTech',
        stage: 'Pre-seed',
        geography: 'MENA',
        business_model_type: 'B2B SaaS',
        funding_asked: 400000,
      })
      onConfirm(result)
    } catch (err) {
      setConfirming(false)
    }
  }

  if (!ocrData) {
    return (
      <div className="flex items-center gap-3 py-8">
        <div className="w-2 h-2 bg-indigo-400 rounded-full animate-ping" />
        <span className="text-slate-400 text-sm">Loading document sections...</span>
      </div>
    )
  }

  const flagged = ocrData.parsing_metadata?.visual_content_flagged || []

  return (
    <div className="space-y-4">
      <div className="mb-5">
        <h2 className="text-slate-100 font-semibold text-lg">Review extracted content before analysis</h2>
        <p className="text-slate-400 text-sm mt-1">
          Confirm or correct the extracted data. Fields marked LOW are less reliable.
        </p>
      </div>

      {ocrData.review_sections.map(section => {
        const isLow  = section.confidence === 'low'
        const isHandwritten = section.source === 'HANDWRITTEN_UNVERIFIED'
        const srcInfo = SOURCE_LABELS[section.source] || { label: section.source, color: 'text-slate-400' }

        return (
          <motion.div
            key={section.section_name}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={`rounded-xl border p-4 space-y-3 ${
              isHandwritten
                ? 'border-red-700/60 bg-red-950/20 border-l-4 border-l-red-500'
                : isLow
                ? 'border-amber-700/60 bg-amber-950/20 border-l-4 border-l-amber-500'
                : 'border-slate-700 bg-slate-800/40'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-slate-100 font-semibold text-sm">{section.section_name}</span>
              <div className="flex items-center gap-2">
                {isHandwritten && (
                  <span className="text-xs text-red-400 font-medium">Handwritten — verify carefully</span>
                )}
                {isLow && !isHandwritten && (
                  <span className="text-xs text-amber-400 font-medium">Review recommended</span>
                )}
                <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${CONFIDENCE_COLORS[section.confidence.toUpperCase()]}`}>
                  {section.confidence.toUpperCase()}
                </span>
              </div>
            </div>

            <textarea
              value={sectionValues[section.section_name] || ''}
              onChange={e => setSectionValues(prev => ({ ...prev, [section.section_name]: e.target.value }))}
              rows={3}
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 resize-none focus:outline-none focus:border-indigo-500 transition-colors"
            />

            <p className={`text-xs ${srcInfo.color}`}>
              Source: {srcInfo.label}
              {section.unclear_count > 0 && (
                <span className="ml-2 text-amber-400">· {section.unclear_count} unclear word{section.unclear_count !== 1 ? 's' : ''}</span>
              )}
            </p>
          </motion.div>
        )
      })}

      {/* Flagged visual content */}
      {flagged.length > 0 && (
        <div className="space-y-3 pt-2">
          {flagged.includes('Slide 4 — bar chart not extractable') && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 space-y-2">
              <p className="text-sm text-slate-400">
                📊 <span className="text-slate-300">Slide 4 — bar chart not extractable.</span> Describe the key data point manually (optional):
              </p>
              <textarea
                value={extraNote}
                onChange={e => setExtraNote(e.target.value)}
                rows={2}
                placeholder="e.g. Growth rate chart shows 3× YoY from 2022 to 2023..."
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-300 resize-none focus:outline-none focus:border-indigo-500 transition-colors placeholder-slate-600"
              />
            </div>
          )}
          {flagged.includes('Slide 6 — team photo not extractable') && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
              <p className="text-sm text-slate-400">
                📸 <span className="text-slate-300">Slide 6 — team photo not extractable.</span> No action needed.
              </p>
            </div>
          )}
        </div>
      )}

      <motion.button
        onClick={handleConfirm}
        disabled={confirming}
        whileHover={{ scale: confirming ? 1 : 1.01 }}
        whileTap={{ scale: confirming ? 1 : 0.99 }}
        className="w-full py-3 rounded-xl bg-green-600 hover:bg-green-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold text-base transition-colors mt-4"
      >
        {confirming ? 'Running analysis...' : 'Confirm and Analyse →'}
      </motion.button>
    </div>
  )
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function OCRAnimationGate({ fileName, onResult }) {
  const [step, setStep] = useState(1)

  const stepLabels = [
    'Quality check',
    'Pre-processing',
    'OCR scanning',
    'Structuring',
    'Review',
  ]

  return (
    <div className="bg-[#1e293b] border border-slate-700 rounded-xl p-6 space-y-6">
      {/* Step indicator */}
      <div className="flex items-center gap-2">
        {stepLabels.map((label, i) => {
          const num = i + 1
          const done = num < step
          const active = num === step
          return (
            <div key={num} className="flex items-center gap-2">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 transition-colors ${
                done   ? 'bg-green-600 text-white' :
                active ? 'bg-indigo-600 text-white' :
                         'bg-slate-700 text-slate-500'
              }`}>
                {done ? '✓' : num}
              </div>
              {num < stepLabels.length && (
                <div className={`h-px w-6 transition-colors ${done ? 'bg-green-600' : 'bg-slate-700'}`} />
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
          transition={{ duration: 0.25 }}
        >
          {step === 1 && <Step1QualityCheck onDone={() => setStep(2)} />}
          {step === 2 && <Step2Preprocessing onDone={() => setStep(3)} />}
          {step === 3 && <Step3Scanning onDone={() => setStep(4)} />}
          {step === 4 && <Step4Structure onDone={() => setStep(5)} />}
          {step === 5 && <Step5ReviewGate onConfirm={onResult} />}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
