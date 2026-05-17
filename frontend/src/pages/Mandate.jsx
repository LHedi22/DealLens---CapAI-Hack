import { useState } from 'react'
import MandateConfigForm from '../components/forms/MandateConfigForm'
import { applyMandate } from '../lib/api'

const CARD = {
  background:   'var(--surface-1)',
  border:       '1px solid var(--border)',
  borderRadius: 20,
  padding:      28,
  boxShadow:    '0 1px 3px rgba(16,24,40,0.06)',
}

export default function Mandate({ onApplied }) {
  const [applyResult, setApplyResult] = useState(null)
  const [applying, setApplying]       = useState(false)

  const handleMandateSaved = async () => {
    setApplying(true)
    try {
      const result = await applyMandate()
      setApplyResult(result)
      setTimeout(() => setApplyResult(null), 8000)
      if (onApplied) onApplied()
    } catch {
      // mandate saved — re-apply is best-effort, silently skip
    } finally {
      setApplying(false)
    }
  }

  const changed = applyResult?.changed_startups?.length > 0

  return (
    <div style={{ maxWidth: 680, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* Page header */}
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
          Fund Mandate
        </h1>
        <p style={{ fontSize: 13, color: 'var(--tx-3)', marginTop: 8, marginBottom: 0, lineHeight: 1.6 }}>
          Define your fund's investment criteria. Hard constraints override AI verdicts — a mandate breach always results in a PASS.
        </p>
      </div>

      {/* Applying indicator */}
      {applying && (
        <div
          style={{
            ...CARD,
            display:    'flex',
            alignItems: 'center',
            gap:        12,
            padding:    '14px 20px',
          }}
        >
          <span
            className="skeleton"
            style={{
              width: 8, height: 8, borderRadius: '50%',
              background: 'var(--gold)', flexShrink: 0,
            }}
          />
          <p style={{ fontSize: 13, color: 'var(--tx-2)', margin: 0 }}>
            Re-applying mandate to pipeline…
          </p>
        </div>
      )}

      {/* Apply result notification */}
      {applyResult && !applying && (
        <div
          style={{
            background:   changed ? 'rgba(110,86,207,0.06)' : 'rgba(16,19,24,0.03)',
            border:       `1px solid ${changed ? 'rgba(110,86,207,0.25)' : 'var(--border)'}`,
            borderRadius: 14,
            padding:      '16px 20px',
          }}
        >
          <p
            style={{
              fontSize:   13,
              fontWeight: 600,
              color:      changed ? 'var(--gold)' : 'var(--tx-2)',
              margin:     changed ? '0 0 10px' : '0',
            }}
          >
            {applyResult.message}
          </p>
          {changed && (
            <ul style={{ margin: 0, paddingLeft: 16, display: 'flex', flexDirection: 'column', gap: 5 }}>
              {applyResult.changed_startups.map((s, i) => (
                <li key={i} style={{ fontSize: 12, color: 'rgba(110,86,207,0.80)' }}>
                  <span style={{ fontWeight: 600, color: 'var(--gold)' }}>{s.startup_name}</span>
                  {' — '}{s.reasons?.join('; ')}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Form card */}
      <div style={CARD}>
        <div style={{ marginBottom: 24 }}>
          <span
            style={{
              fontSize:      10,
              fontWeight:    500,
              color:         'var(--tx-3)',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
            }}
          >
            Investment Criteria
          </span>
        </div>
        <MandateConfigForm onSaved={handleMandateSaved} />
      </div>

    </div>
  )
}
