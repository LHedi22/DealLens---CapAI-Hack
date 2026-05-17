import { useState } from 'react'
import { submitProfile } from '../../lib/api'

const SECTORS = ['EdTech', 'FinTech', 'HealthTech', 'Logistics', 'SaaS', 'AgriTech', 'E-Commerce', 'CleanTech', 'Manufacturing', 'Construction Tech', 'Other']
const STAGES = ['Pre-seed', 'Seed', 'Series A', 'Series B+']
const GEOS = ['MENA', 'Europe', 'North America', 'Sub-Saharan Africa', 'South/Southeast Asia', 'LATAM', 'Other']
const MODELS = ['SaaS', 'Marketplace', 'Hardware', 'Services', 'Deep Tech', 'Consumer App', 'Other']

function Field({ label, children }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium text-slate-300">{label}</label>
      {children}
    </div>
  )
}

function Select({ value, onChange, options, placeholder, disabled }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      disabled={disabled}
      className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <option value="" disabled>{placeholder}</option>
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  )
}

export default function StartupProfileForm({ onSubmit, disabled = false }) {
  const [form, setForm] = useState({
    startup_name: '',
    sector: '',
    stage: '',
    geography: '',
    funding_asked: '',
    business_model_type: '',
  })
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }))

  const valid = form.startup_name && form.sector && form.stage && form.geography && form.business_model_type

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!valid) return
    setLoading(true)
    try {
      const payload = {
        ...form,
        funding_asked: form.funding_asked ? parseInt(form.funding_asked) : null,
      }
      await submitProfile(payload)
      setToast({ type: 'success', msg: `Profile saved for ${form.startup_name}` })
      if (onSubmit) onSubmit(payload)
      setTimeout(() => setToast(null), 3000)
    } catch {
      setToast({ type: 'error', msg: 'Failed to save profile. Is the backend running?' })
      setTimeout(() => setToast(null), 4000)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className={`space-y-4 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      <Field label="Startup Name">
        <input
          type="text"
          value={form.startup_name}
          onChange={e => set('startup_name', e.target.value)}
          placeholder="e.g. NovaPay"
          disabled={disabled}
          className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 placeholder:text-slate-600 disabled:cursor-not-allowed"
        />
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Sector">
          <Select value={form.sector} onChange={v => set('sector', v)} options={SECTORS} placeholder="Select sector" disabled={disabled} />
        </Field>
        <Field label="Stage">
          <Select value={form.stage} onChange={v => set('stage', v)} options={STAGES} placeholder="Select stage" disabled={disabled} />
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Geography">
          <Select value={form.geography} onChange={v => set('geography', v)} options={GEOS} placeholder="Select region" disabled={disabled} />
        </Field>
        <Field label="Business Model">
          <Select value={form.business_model_type} onChange={v => set('business_model_type', v)} options={MODELS} placeholder="Select model" disabled={disabled} />
        </Field>
      </div>

      <Field label="Funding Ask (USD) — optional">
        <input
          type="number"
          value={form.funding_asked}
          onChange={e => set('funding_asked', e.target.value)}
          placeholder="e.g. 500000"
          disabled={disabled}
          className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 placeholder:text-slate-600 disabled:cursor-not-allowed"
        />
      </Field>

      {toast && (
        <div className={`px-4 py-2.5 rounded-lg text-sm ${toast.type === 'success' ? 'bg-green-900/50 text-green-300 border border-green-700' : 'bg-red-900/50 text-red-300 border border-red-700'}`}>
          {toast.msg}
        </div>
      )}

      <button
        type="submit"
        disabled={disabled || !valid || loading}
        className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-sm transition-colors"
      >
        {loading ? 'Analysing...' : 'Analyse Startup →'}
      </button>
    </form>
  )
}
