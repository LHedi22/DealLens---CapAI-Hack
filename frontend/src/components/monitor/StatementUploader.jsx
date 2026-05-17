import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { uploadMonitorStatement, markNoStatement } from '../../lib/api'
import MonitorOCRAnimationGate from './MonitorOCRAnimationGate'

const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/jpg']

function currentMonth() {
  return new Date().toISOString().slice(0, 7)
}

export default function StatementUploader({ startupName, onUploaded }) {
  const [phase, setPhase]       = useState('idle')   // idle | uploading | ocr | done | error | no-statement
  const [result, setResult]     = useState(null)
  const [error, setError]       = useState(null)
  const [pendingFile, setPendingFile] = useState(null)

  const onDrop = useCallback(async (files) => {
    if (!files.length) return
    const file = files[0]

    if (IMAGE_TYPES.includes(file.type)) {
      setPendingFile(file)
      setPhase('ocr')
      return
    }

    setPhase('uploading')
    setResult(null)
    setError(null)
    try {
      const data = await uploadMonitorStatement(startupName, file)
      setResult(data)
      setPhase('done')
      if (onUploaded) onUploaded(data)
    } catch (e) {
      setError(e.message || 'Upload failed — check that the backend is running.')
      setPhase('error')
    }
  }, [startupName, onUploaded])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg':      ['.jpg', '.jpeg'],
      'image/png':       ['.png'],
    },
    maxFiles: 1,
    disabled: phase === 'uploading',
  })

  async function handleNoStatement() {
    setPhase('uploading')
    setError(null)
    try {
      const data = await markNoStatement(startupName, currentMonth())
      setResult({ ...data, _no_statement: true })
      setPhase('done')
      if (onUploaded) onUploaded(data)
    } catch (e) {
      setError(e.message || 'Failed to mark no-statement.')
      setPhase('error')
    }
  }

  function handleOcrResult(data) {
    setResult(data)
    setPendingFile(null)
    setPhase('done')
    if (onUploaded) onUploaded(data)
  }

  if (phase === 'ocr' && pendingFile) {
    return (
      <MonitorOCRAnimationGate
        startupName={startupName}
        fileName={pendingFile.name}
        onResult={handleOcrResult}
      />
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors ${
          isDragActive          ? 'border-indigo-500 bg-indigo-950/30 cursor-copy' :
          phase === 'uploading' ? 'border-slate-600 bg-slate-800/20 cursor-not-allowed opacity-60' :
                                  'border-slate-600 bg-slate-800/20 hover:border-slate-500 cursor-pointer'
        }`}
      >
        <input {...getInputProps()} />

        {phase === 'uploading' ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-5 h-5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-400 text-sm">Parsing statement and classifying transactions…</p>
            <p className="text-slate-600 text-xs">This may take a moment if Ollama is resolving ambiguous transactions.</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-1">
            <svg className="w-6 h-6 text-slate-500 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <p className="text-slate-300 text-sm font-medium">
              {isDragActive ? 'Drop bank statement here' : 'Upload monthly bank statement'}
            </p>
            <p className="text-slate-500 text-xs">PDF or image (JPG, PNG) — drag & drop or click to browse</p>
          </div>
        )}
      </div>

      {phase === 'idle' && (
        <button
          onClick={handleNoStatement}
          className="text-xs text-slate-500 hover:text-amber-400 transition-colors self-start underline underline-offset-2"
        >
          No statement received this month?
        </button>
      )}

      <AnimatePresence>
        {phase === 'done' && result && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className={`border rounded-lg px-4 py-3 flex flex-col gap-2 ${
              result._no_statement
                ? 'bg-amber-950/40 border-amber-700'
                : 'bg-green-950/40 border-green-700'
            }`}
          >
            <p className={`font-semibold text-sm ${result._no_statement ? 'text-amber-300' : 'text-green-300'}`}>
              {result._no_statement ? 'No-statement alert raised' : 'Statement processed'}
            </p>

            {!result._no_statement && (
              <div className="flex flex-wrap gap-5 text-xs text-slate-300">
                <span>
                  <span className="text-slate-500">Transactions: </span>
                  {result.transaction_count}
                </span>
                <span>
                  <span className="text-slate-500">Auto-classified: </span>
                  <span className="text-blue-300">{result.auto_classified}</span>
                </span>
                {result.unclassified > 0 && (
                  <span>
                    <span className="text-slate-500">Needs review: </span>
                    <span className="text-red-300 font-medium">{result.unclassified}</span>
                  </span>
                )}
                {result.compliance_health_score != null && (
                  <span>
                    <span className="text-slate-500">New health score: </span>
                    <span className="font-bold text-white">{result.compliance_health_score}</span>
                  </span>
                )}
              </div>
            )}

            {result._no_statement && result.compliance_health_score != null && (
              <p className="text-xs text-slate-300">
                Health score updated to{' '}
                <span className="font-bold text-white">{result.compliance_health_score}</span>
                {' '}— a NO_STATEMENT alert has been logged.
              </p>
            )}

            {!result._no_statement && result.unclassified > 0 && (
              <p className="text-amber-400 text-xs">
                ↓ {result.unclassified} transaction{result.unclassified > 1 ? 's require' : ' requires'} manual review — click the red badge below to reclassify.
              </p>
            )}

            <button
              onClick={() => { setPhase('idle'); setResult(null) }}
              className="text-xs text-slate-500 hover:text-slate-300 self-end transition-colors"
            >
              Upload another
            </button>
          </motion.div>
        )}

        {phase === 'error' && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="bg-red-950/40 border border-red-700 rounded-lg px-4 py-3 flex flex-col gap-2"
          >
            <p className="text-red-300 text-sm font-medium">Upload failed</p>
            <p className="text-red-400 text-xs">{error}</p>
            <button
              onClick={() => { setPhase('idle'); setError(null) }}
              className="text-xs text-slate-400 hover:text-white self-start transition-colors"
            >
              Try again
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
