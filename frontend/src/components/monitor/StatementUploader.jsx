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
  const [phase, setPhase]           = useState('idle')
  const [result, setResult]         = useState(null)
  const [error, setError]           = useState(null)
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

  const dropBorder = isDragActive
    ? '2px dashed #6E56CF'
    : phase === 'uploading'
    ? '2px dashed #D0D4DC'
    : '2px dashed #D0D4DC'

  const dropBg = isDragActive
    ? 'rgba(110,86,207,0.06)'
    : 'var(--surface-2)'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div
        {...getRootProps()}
        style={{
          border: dropBorder, borderRadius: 14, padding: '24px',
          textAlign: 'center', cursor: phase === 'uploading' ? 'not-allowed' : 'pointer',
          background: dropBg, transition: 'all 0.15s',
          opacity: phase === 'uploading' ? 0.6 : 1,
        }}
      >
        <input {...getInputProps()} />

        {phase === 'uploading' ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 20, height: 20, border: '2px solid #6E56CF',
              borderTopColor: 'transparent', borderRadius: '50%',
              animation: 'spin 0.75s linear infinite',
            }} />
            <p style={{ fontSize: 13, color: 'var(--tx-2)', margin: 0 }}>
              Parsing statement and classifying transactions…
            </p>
            <p style={{ fontSize: 11, color: 'var(--tx-3)', margin: 0 }}>
              This may take a moment if Ollama is resolving ambiguous transactions.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
            <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: isDragActive ? '#6E56CF' : 'var(--tx-3)', marginBottom: 4 }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <p style={{ fontSize: 13, fontWeight: 600, color: isDragActive ? '#6E56CF' : 'var(--tx-1)', margin: 0 }}>
              {isDragActive ? 'Drop bank statement here' : 'Upload monthly bank statement'}
            </p>
            <p style={{ fontSize: 11, color: 'var(--tx-3)', margin: 0 }}>
              PDF or image (JPG, PNG) — drag & drop or click to browse
            </p>
          </div>
        )}
      </div>

      {phase === 'idle' && (
        <button
          onClick={handleNoStatement}
          style={{
            fontSize: 12, color: 'var(--tx-3)', background: 'none',
            border: 'none', cursor: 'pointer', alignSelf: 'flex-start',
            textDecoration: 'underline', textUnderlineOffset: 2, transition: 'color 0.15s',
          }}
        >
          No statement received this month?
        </button>
      )}

      <AnimatePresence>
        {phase === 'done' && result && (
          <motion.div
            initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            style={{
              border: `1px solid ${result._no_statement ? 'rgba(245,165,36,0.22)' : 'rgba(18,183,106,0.22)'}`,
              background: result._no_statement ? 'rgba(245,165,36,0.06)' : 'rgba(18,183,106,0.06)',
              borderRadius: 12, padding: '14px 16px',
              display: 'flex', flexDirection: 'column', gap: 8,
            }}
          >
            <p style={{
              fontSize: 13, fontWeight: 600, margin: 0,
              color: result._no_statement ? '#92400E' : '#065F46',
            }}>
              {result._no_statement ? 'No-statement alert raised' : 'Statement processed'}
            </p>

            {!result._no_statement && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, fontSize: 12, color: 'var(--tx-2)' }}>
                <span><span style={{ color: 'var(--tx-3)' }}>Transactions: </span>{result.transaction_count}</span>
                <span>
                  <span style={{ color: 'var(--tx-3)' }}>Auto-classified: </span>
                  <span style={{ color: '#1E40AF', fontWeight: 600 }}>{result.auto_classified}</span>
                </span>
                {result.unclassified > 0 && (
                  <span>
                    <span style={{ color: 'var(--tx-3)' }}>Needs review: </span>
                    <span style={{ color: '#991B1B', fontWeight: 700 }}>{result.unclassified}</span>
                  </span>
                )}
                {result.compliance_health_score != null && (
                  <span>
                    <span style={{ color: 'var(--tx-3)' }}>New health score: </span>
                    <span style={{ fontWeight: 700, color: 'var(--tx-1)' }}>{result.compliance_health_score}</span>
                  </span>
                )}
              </div>
            )}

            {result._no_statement && result.compliance_health_score != null && (
              <p style={{ fontSize: 12, color: 'var(--tx-2)', margin: 0 }}>
                Health score updated to{' '}
                <span style={{ fontWeight: 700, color: 'var(--tx-1)' }}>{result.compliance_health_score}</span>
                {' '}— a NO_STATEMENT alert has been logged.
              </p>
            )}

            {!result._no_statement && result.unclassified > 0 && (
              <p style={{ fontSize: 12, color: '#D97706', margin: 0 }}>
                ↓ {result.unclassified} transaction{result.unclassified > 1 ? 's require' : ' requires'} manual review — click the red badge below to reclassify.
              </p>
            )}

            <button
              onClick={() => { setPhase('idle'); setResult(null) }}
              style={{
                fontSize: 12, color: 'var(--tx-3)', background: 'none',
                border: 'none', cursor: 'pointer', alignSelf: 'flex-end',
                transition: 'color 0.15s',
              }}
            >
              Upload another
            </button>
          </motion.div>
        )}

        {phase === 'error' && (
          <motion.div
            initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            style={{
              background: 'rgba(240,68,56,0.06)', border: '1px solid rgba(240,68,56,0.22)',
              borderRadius: 12, padding: '14px 16px',
              display: 'flex', flexDirection: 'column', gap: 6,
            }}
          >
            <p style={{ fontSize: 13, fontWeight: 600, color: '#DC2626', margin: 0 }}>Upload failed</p>
            <p style={{ fontSize: 12, color: '#EF4444', margin: 0 }}>{error}</p>
            <button
              onClick={() => { setPhase('idle'); setError(null) }}
              style={{
                fontSize: 12, color: 'var(--tx-3)', background: 'none',
                border: 'none', cursor: 'pointer', alignSelf: 'flex-start',
                transition: 'color 0.15s',
              }}
            >
              Try again
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
