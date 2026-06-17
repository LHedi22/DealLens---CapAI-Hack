import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import FileUploader from '../components/upload/FileUploader'
import OCRAnimationGate from '../components/upload/OCRAnimationGate'
import StartupProfileForm from '../components/forms/StartupProfileForm'
import ScorecardCard from '../components/cards/ScorecardCard'
import ESGCard from '../components/cards/ESGCard'
import MemoryInsightCard from '../components/cards/MemoryInsightCard'
import ForecastCard from '../components/cards/ForecastCard'
import FixAnalysisCard from '../components/cards/FixAnalysisCard'
import PortfolioFitCard from '../components/cards/PortfolioFitCard'
import BlindSpotCard from '../components/cards/BlindSpotCard'
import {
  ScorecardSkeleton, ESGSkeleton, MemorySkeleton,
  ForecastSkeleton, FixSkeleton, PortfolioSkeleton, BlindSpotSkeleton,
} from '../components/shared/LoadingCards'
import { evaluateStartup, getCachedEvaluation } from '../lib/api'

const LOADING_STEPS = [
  'Extracting documents...',
  'Scoring business fundamentals...',
  'Analysing ESG dimensions...',
  'Checking memory layer...',
  'Forecasting revenue trajectory...',
  'Analysing fix worthiness...',
  'Mapping portfolio fit...',
  'Generating blind spots...',
  'Generating recommendation...',
]

const TIMEOUT_WARN_MS = 360_000

const CARD = {
  background:   'var(--surface-1)',
  border:       '1px solid var(--border)',
  borderRadius: 20,
  padding:      28,
}

function generateId() {
  return `startup_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
}

function isOllamaError(msg) {
  const lower = (msg || '').toLowerCase()
  return lower.includes('ollama') || lower.includes('ai engine') || lower.includes('503')
}

// ── Ollama offline ────────────────────────────────────────────────────────────
function OllamaOfflineCard({ onRetry }) {
  return (
    <div style={{ maxWidth: 680, margin: '0 auto' }}>
      <div
        style={{
          ...CARD,
          textAlign: 'center',
          padding: 48,
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20,
        }}
      >
        <div style={{ fontSize: 48, lineHeight: 1 }}>🔌</div>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--tx-1)', margin: '0 0 8px', fontFamily: 'Outfit, Inter, system-ui, sans-serif' }}>
            AI Engine Offline
          </h2>
          <p style={{ fontSize: 13, color: 'var(--tx-2)', margin: 0, lineHeight: 1.6 }}>
            Ollama is not running. Start it with the commands below, then retry.
          </p>
        </div>
        <div
          style={{
            background:   'var(--surface-2)',
            border:       '1px solid var(--border)',
            borderRadius: 12,
            padding:      '16px 20px',
            textAlign:    'left',
            width:        '100%',
            fontFamily:   'JetBrains Mono, monospace',
            fontSize:     12,
            lineHeight:   2,
          }}
        >
          <div style={{ color: 'var(--s-green)' }}>ollama serve</div>
          <div style={{ color: 'var(--tx-3)' }}># in a second terminal:</div>
          <div style={{ color: 'var(--s-green)' }}>ollama pull mistral</div>
        </div>
        <button
          onClick={onRetry}
          onMouseEnter={e => (e.currentTarget.style.opacity = '0.82')}
          onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
          style={{
            padding: '10px 24px', borderRadius: 10,
            background: 'var(--gold)', color: '#FFFFFF',
            fontSize: 13, fontWeight: 600, border: 'none', cursor: 'pointer',
            transition: 'opacity 0.15s',
          }}
        >
          Retry
        </button>
      </div>
    </div>
  )
}

// ── Physical scan banner ──────────────────────────────────────────────────────
function PhysicalScanBanner({ ocrConfidence }) {
  const pct = ocrConfidence ? Math.round(ocrConfidence * 100) : 71
  return (
    <div
      style={{
        background:   'rgba(110,86,207,0.06)',
        border:       '1px solid rgba(110,86,207,0.22)',
        borderRadius: 14,
        padding:      '12px 18px',
        fontSize:     13,
        color:        'var(--gold)',
        lineHeight:   1.6,
      }}
    >
      📄 This analysis was generated from a physical document scan (OCR confidence: {pct}%).
      Fields confirmed by the investor are given full weight. Treat LOW confidence sections with additional scrutiny.
    </div>
  )
}

// ── Results view ──────────────────────────────────────────────────────────────
function ResultsView({ result, onReset, isCached }) {
  const hasBreach  = !!result.mandate_breach
  const hasFlags   = !hasBreach && result.mandate_flags?.length > 0
  const isPhysical = result.source_type === 'PHYSICAL_SCAN'
  const filesCount = result.files_analysed ?? 1

  const cardVariants = {
    hidden:  { opacity: 0, y: 18 },
    visible: i => ({
      opacity: 1, y: 0,
      transition: { delay: i * 0.10, duration: 0.38, ease: 'easeOut' },
    }),
  }

  return (
    <div style={{ maxWidth: 720, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 4 }}>
        <div>
          <h1
            style={{
              fontFamily:    'Outfit, Inter, system-ui, sans-serif',
              fontSize:      34,
              fontWeight:    700,
              color:         'var(--tx-1)',
              margin:        0,
              letterSpacing: '-0.02em',
              lineHeight:    1,
            }}
          >
            {result.startup_name}
          </h1>
          <p style={{ fontSize: 13, color: 'var(--tx-3)', marginTop: 8, marginBottom: 0 }}>
            {isCached
              ? 'Pre-cached evaluation'
              : `${filesCount} document${filesCount !== 1 ? 's' : ''} analysed`}
          </p>
        </div>
        <button
          onClick={onReset}
          onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--border-med)')}
          onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
          style={{
            fontSize: 12, color: 'var(--tx-2)',
            background: 'none',
            border: '1px solid var(--border)',
            borderRadius: 10,
            padding: '7px 14px',
            cursor: 'pointer',
            transition: 'border-color 0.15s',
          }}
        >
          New evaluation
        </button>
      </div>

      {/* Physical scan notice */}
      {isPhysical && <PhysicalScanBanner ocrConfidence={result.ocr_confidence} />}

      {/* Mandate breach */}
      {hasBreach && (
        <div
          style={{
            background:   'rgba(232,69,69,0.06)',
            border:       '1px solid rgba(232,69,69,0.22)',
            borderRadius: 14,
            padding:      '14px 18px',
          }}
        >
          <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--s-red)', margin: '0 0 6px' }}>
            Mandate Breach — Verdict overridden to PASS
          </p>
          {result.mandate_flags?.length > 0 && (
            <ul style={{ margin: 0, paddingLeft: 16, display: 'flex', flexDirection: 'column', gap: 3 }}>
              {result.mandate_flags.map((f, i) => (
                <li key={i} style={{ fontSize: 12, color: 'rgba(232,69,69,0.85)' }}>{f}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Mandate advisory */}
      {hasFlags && (
        <div
          style={{
            background:   'rgba(110,86,207,0.06)',
            border:       '1px solid rgba(110,86,207,0.22)',
            borderRadius: 14,
            padding:      '14px 18px',
          }}
        >
          <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--gold)', margin: '0 0 6px' }}>
            Mandate Advisory Flags
          </p>
          <ul style={{ margin: 0, paddingLeft: 16, display: 'flex', flexDirection: 'column', gap: 3 }}>
            {result.mandate_flags.map((f, i) => (
              <li key={i} style={{ fontSize: 12, color: 'rgba(200,169,74,0.85)' }}>{f}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 8 output cards — staggered reveal */}
      {[
        <ScorecardCard   key="scorecard" data={result} />,
        <ESGCard         key="esg"       data={result} />,
        <MemoryInsightCard key="memory"  memoryData={{
          conviction_delta:   result.conviction_delta,
          delta_explanation:  result.delta_explanation,
          top_memory_matches: result.top_memory_matches || [],
          sector_conviction:  result.sector_conviction  || {},
        }} />,
        <ForecastCard    key="forecast"  forecast={result.forecast} />,
        <FixAnalysisCard key="fix"       fixData={result.fix_analysis} />,
        <PortfolioFitCard key="portfolio" portfolio={result.portfolio} />,
        <BlindSpotCard   key="blind"     blindSpots={result.blind_spots} />,
      ].map((card, i) => (
        <motion.div key={i} custom={i} variants={cardVariants} initial="hidden" animate="visible">
          {card}
        </motion.div>
      ))}
    </div>
  )
}

// ── Step header helper ────────────────────────────────────────────────────────
function StepHeader({ num, label, sub, done, active }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20 }}>
      <div
        style={{
          width: 30, height: 30, borderRadius: '50%', flexShrink: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 12, fontWeight: 700,
          fontFamily: 'JetBrains Mono, monospace',
          background: done
            ? 'rgba(47,204,128,0.15)'
            : active
            ? 'rgba(200,169,74,0.15)'
            : 'rgba(255,255,255,0.04)',
          border: `1px solid ${done ? 'rgba(47,204,128,0.35)' : active ? 'rgba(200,169,74,0.35)' : 'var(--border)'}`,
          color: done ? 'var(--s-green)' : active ? 'var(--gold)' : 'var(--tx-3)',
        }}
      >
        {done ? '✓' : num}
      </div>
      <div>
        <div style={{ fontSize: 14, fontWeight: 600, color: active || done ? 'var(--tx-1)' : 'var(--tx-2)' }}>
          {label}
        </div>
        <div style={{ fontSize: 11, color: 'var(--tx-3)', marginTop: 2 }}>{sub}</div>
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export default function Evaluate({ onEvaluationComplete }) {
  const [searchParams] = useSearchParams()
  const cachedParam = searchParams.get('cached')

  const [startupId]    = useState(generateId)
  const [uploadDone, setUploadDone] = useState(false)
  const [imageFile, setImageFile]   = useState(null)
  const [phase, setPhase]           = useState('setup')
  const [loadingStep, setLoadingStep] = useState(0)
  const [result, setResult]         = useState(null)
  const [errorMsg, setErrorMsg]     = useState('')
  const [timedOut, setTimedOut]     = useState(false)
  const [fileError, setFileError]   = useState('')

  const timeoutRef = useRef(null)
  const stepRef    = useRef(null)

  useEffect(() => {
    if (!cachedParam) return
    setPhase('loading')
    getCachedEvaluation(cachedParam)
      .then(data => {
        if (data) { setResult(data); setPhase('cached') }
        else { setErrorMsg(`No cached evaluation for "${cachedParam}".`); setPhase('error') }
      })
      .catch(() => { setErrorMsg(`Could not load cached evaluation for "${cachedParam}".`); setPhase('error') })
  }, [cachedParam])

  useEffect(() => {
    if (phase !== 'loading') { clearInterval(stepRef.current); return }
    stepRef.current = setInterval(() => setLoadingStep(s => (s + 1) % LOADING_STEPS.length), 2500)
    return () => clearInterval(stepRef.current)
  }, [phase])

  useEffect(() => {
    if (phase === 'loading' && !cachedParam) {
      timeoutRef.current = setTimeout(() => setTimedOut(true), TIMEOUT_WARN_MS)
    }
    return () => { clearTimeout(timeoutRef.current); setTimedOut(false) }
  }, [phase, cachedParam])

  function handleImageDetected(fileName) { setImageFile(fileName); setPhase('ocr') }

  function handleOcrResult(data) {
    setResult(data); setPhase('results')
    if (onEvaluationComplete) onEvaluationComplete()
  }

  async function handleProfileSubmit(profile) {
    if (!uploadDone) { setFileError('Please upload at least one document before submitting.'); return }
    setFileError(''); setPhase('loading'); setLoadingStep(0)
    try {
      const data = await evaluateStartup({
        startup_id: startupId, startup_name: profile.startup_name,
        sector: profile.sector, stage: profile.stage, geography: profile.geography,
        funding_asked: profile.funding_asked ? Number(profile.funding_asked) : null,
        business_model_type: profile.business_model_type,
      })
      setResult(data); setPhase('results')
      if (onEvaluationComplete) onEvaluationComplete()
    } catch (err) { setErrorMsg(err.message || 'Evaluation failed'); setPhase('error') }
  }

  function resetToSetup() {
    setPhase('setup'); setResult(null); setErrorMsg(''); setImageFile(null)
    setUploadDone(false); setTimedOut(false); setFileError('')
  }

  // ── OCR phase ──
  if (phase === 'ocr') {
    return (
      <div style={{ maxWidth: 720, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ fontFamily: 'Outfit, Inter, system-ui, sans-serif', fontSize: 30, fontWeight: 700, color: 'var(--tx-1)', margin: 0, letterSpacing: '-0.02em' }}>
              Physical Document Scan
            </h1>
            <p style={{ fontSize: 13, color: 'var(--tx-3)', marginTop: 6, marginBottom: 0 }}>
              Image detected — running OCR pipeline
            </p>
          </div>
          <button
            onClick={resetToSetup}
            style={{
              fontSize: 12, color: 'var(--tx-2)', background: 'none',
              border: '1px solid var(--border)', borderRadius: 10, padding: '7px 14px', cursor: 'pointer',
            }}
          >
            ← Cancel
          </button>
        </div>
        <OCRAnimationGate fileName={imageFile} onResult={handleOcrResult} />
      </div>
    )
  }

  // ── Loading phase ──
  if (phase === 'loading') {
    return (
      <div style={{ maxWidth: 720, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
        {timedOut && (
          <div style={{
            background: 'rgba(110,86,207,0.06)', border: '1px solid rgba(110,86,207,0.22)',
            borderRadius: 12, padding: '12px 18px', fontSize: 13, color: 'var(--gold)',
          }}>
            Analysis is taking longer than expected — Ollama may be under load. Still working…
          </div>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '6px 0' }}>
          <span
            className="skeleton"
            style={{
              width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
              background: 'var(--gold)',
              boxShadow: '0 0 6px rgba(200,169,74,0.5)',
            }}
          />
          <span style={{ fontSize: 13, color: 'var(--gold)', fontFamily: 'JetBrains Mono, monospace' }}>
            {LOADING_STEPS[loadingStep]}
          </span>
        </div>
        <ScorecardSkeleton />
        <ESGSkeleton />
        <MemorySkeleton />
        <ForecastSkeleton />
        <FixSkeleton />
        <PortfolioSkeleton />
        <BlindSpotSkeleton />
      </div>
    )
  }

  // ── Error phase ──
  if (phase === 'error') {
    if (isOllamaError(errorMsg)) return <OllamaOfflineCard onRetry={resetToSetup} />
    return (
      <div style={{ maxWidth: 720, margin: '0 auto' }}>
        <div style={{
          background: 'rgba(232,69,69,0.06)', border: '1px solid rgba(232,69,69,0.22)',
          borderRadius: 20, padding: '28px 32px',
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--s-red)', margin: '0 0 10px', fontFamily: 'Outfit, Inter, system-ui, sans-serif' }}>
            Evaluation Failed
          </h2>
          <p style={{ fontSize: 13, color: 'var(--tx-2)', margin: '0 0 16px', lineHeight: 1.6 }}>{errorMsg}</p>
          <button
            onClick={resetToSetup}
            style={{ fontSize: 13, color: 'var(--gold)', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline', padding: 0 }}
          >
            ← Try again
          </button>
        </div>
      </div>
    )
  }

  // ── Results / cached phase ──
  if ((phase === 'results' || phase === 'cached') && result) {
    return <ResultsView result={result} onReset={resetToSetup} isCached={phase === 'cached'} />
  }

  // ── Setup phase ──
  return (
    <div style={{ maxWidth: 720, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* Page header */}
      <div>
        <h1
          style={{
            fontFamily: 'Outfit, Inter, system-ui, sans-serif', fontSize: 34, fontWeight: 700,
            color: 'var(--tx-1)', margin: 0, letterSpacing: '-0.02em', lineHeight: 1,
          }}
        >
          New Evaluation
        </h1>
        <p style={{ fontSize: 13, color: 'var(--tx-3)', marginTop: 8, marginBottom: 0, lineHeight: 1.5 }}>
          Upload startup documents and fill the profile to generate a full investment scorecard.
        </p>
      </div>

      {/* Step 1 — Upload */}
      <div style={CARD}>
        <StepHeader
          num="1"
          label="Upload Documents"
          sub="Pitch deck, financials, term sheet — any combination. Upload an image to trigger OCR demo."
          done={uploadDone}
          active={true}
        />
        <FileUploader
          startupId={startupId}
          onUploadComplete={() => setUploadDone(true)}
          onImageDetected={handleImageDetected}
        />
        {fileError && (
          <p style={{ fontSize: 12, color: 'var(--s-red)', marginTop: 12 }}>{fileError}</p>
        )}
      </div>

      {/* Step 2 — Profile */}
      <div
        style={{
          ...CARD,
          opacity: uploadDone ? 1 : 0.6,
          transition: 'opacity 0.2s',
        }}
      >
        <StepHeader
          num="2"
          label="Startup Profile"
          sub="Six fields — used for mandate filtering and memory matching."
          done={false}
          active={uploadDone}
        />
        {!uploadDone && (
          <p style={{ fontSize: 12, color: 'var(--tx-3)', fontStyle: 'italic', marginBottom: 16 }}>
            Upload at least one document first to unlock this step.
          </p>
        )}
        <StartupProfileForm disabled={!uploadDone} onSubmit={handleProfileSubmit} />
      </div>

    </div>
  )
}
