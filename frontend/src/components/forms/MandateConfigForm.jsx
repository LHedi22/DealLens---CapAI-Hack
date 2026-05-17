import { useState, useEffect } from 'react'
import { getMandate, saveMandate } from '../../lib/api'

const SECTORS = ['EdTech', 'FinTech', 'HealthTech', 'Logistics', 'SaaS', 'AgriTech', 'E-Commerce', 'CleanTech', 'Manufacturing', 'Construction Tech']
const STAGES = ['Pre-seed', 'Seed', 'Series A', 'Series B+']
const GEOS = ['MENA', 'Europe', 'North America', 'Sub-Saharan Africa', 'South/Southeast Asia', 'LATAM']
const ESG_AXES = ['Balanced', 'E-priority', 'S-priority', 'G-priority']

function CheckGroup({ options, selected, onChange }) {
  const toggle = (val) => {
    if (selected.includes(val)) onChange(selected.filter(v => v !== val))
    else onChange([...selected, val])
  }
  return (
    <div className="flex flex-wrap gap-2">
      {options.map(opt => (
        <button
          key={opt}
          type="button"
          onClick={() => toggle(opt)}
          className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
            selected.includes(opt)
              ? 'bg-indigo-600 border-indigo-500 text-white'
              : 'bg-slate-800 border-slate-600 text-slate-400 hover:border-slate-500 hover:text-slate-200'
          }`}
        >
          {opt}
        </button>
      ))}
    </div>
  )
}

function Field({ label, hint, children }) {
  return (
    <div className="space-y-2">
      <div>
        <label className="block text-sm font-medium text-slate-300">{label}</label>
        {hint && <p className="text-xs text-slate-500 mt-0.5">{hint}</p>}
      </div>
      {children}
    </div>
  )
}

const DEFAULT = {
  sector_focus: [],
  stage_preference: [],
  geography_scope: [],
  min_esg_threshold: 0,
  ticket_size_min: '',
  ticket_size_max: '',
  esg_priority_axis: 'Balanced',
}

export default function MandateConfigForm({ onSaved }) {
  const [form, setForm] = useState(DEFAULT)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    getMandate()
      .then(data => setForm({
        sector_focus: data.sector_focus ?? [],
        stage_preference: data.stage_preference ?? [],
        geography_scope: data.geography_scope ?? [],
        min_esg_threshold: data.min_esg_threshold ?? 0,
        ticket_size_min: data.ticket_size_min ?? '',
        ticket_size_max: data.ticket_size_max ?? '',
        esg_priority_axis: data.esg_priority_axis ?? 'Balanced',
      }))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }))

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        ...form,
        ticket_size_min: form.ticket_size_min ? parseInt(form.ticket_size_min) : null,
        ticket_size_max: form.ticket_size_max ? parseInt(form.ticket_size_max) : null,
        sector_focus: form.sector_focus.length ? form.sector_focus : null,
        stage_preference: form.stage_preference.length ? form.stage_preference : null,
        geography_scope: form.geography_scope.length ? form.geography_scope : null,
      }
      await saveMandate(payload)
      setToast({ type: 'success', msg: 'Mandate saved successfully.' })
      if (onSaved) onSaved()
    } catch {
      setToast({ type: 'error', msg: 'Failed to save. Is the backend running?' })
    } finally {
      setSaving(false)
      setTimeout(() => setToast(null), 3000)
    }
  }

  if (loading) return (
    <div className="space-y-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="h-10 bg-slate-800 rounded-lg animate-pulse" />
      ))}
    </div>
  )

  return (
    <form onSubmit={handleSave} className="space-y-6">
      <Field label="Sector Focus" hint="Leave empty to accept all sectors">
        <CheckGroup options={SECTORS} selected={form.sector_focus} onChange={v => set('sector_focus', v)} />
      </Field>

      <Field label="Stage Preference" hint="Leave empty to accept all stages">
        <CheckGroup options={STAGES} selected={form.stage_preference} onChange={v => set('stage_preference', v)} />
      </Field>

      <Field label="Geography Scope" hint="Leave empty to accept all regions">
        <CheckGroup options={GEOS} selected={form.geography_scope} onChange={v => set('geography_scope', v)} />
      </Field>

      <Field label={`Minimum ESG Threshold: ${form.min_esg_threshold}`} hint="Startups below this ESG score are hard-passed regardless of business score">
        <input
          type="range"
          min={0}
          max={100}
          step={5}
          value={form.min_esg_threshold}
          onChange={e => set('min_esg_threshold', parseInt(e.target.value))}
          className="w-full accent-indigo-500"
        />
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>0 (disabled)</span>
          <span>50 (moderate)</span>
          <span>100 (strict)</span>
        </div>
      </Field>

      <Field label="Ticket Size Range (USD)">
        <div className="flex gap-3 items-center">
          <input
            type="number"
            value={form.ticket_size_min}
            onChange={e => set('ticket_size_min', e.target.value)}
            placeholder="Min (e.g. 100000)"
            className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-indigo-500 placeholder:text-slate-600"
          />
          <span className="text-slate-500">—</span>
          <input
            type="number"
            value={form.ticket_size_max}
            onChange={e => set('ticket_size_max', e.target.value)}
            placeholder="Max (e.g. 2000000)"
            className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-indigo-500 placeholder:text-slate-600"
          />
        </div>
      </Field>

      <Field label="ESG Priority Axis">
        <div className="flex gap-3 flex-wrap">
          {ESG_AXES.map(axis => (
            <label key={axis} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="esg_axis"
                value={axis}
                checked={form.esg_priority_axis === axis}
                onChange={() => set('esg_priority_axis', axis)}
                className="accent-indigo-500"
              />
              <span className="text-sm text-slate-300">{axis}</span>
            </label>
          ))}
        </div>
      </Field>

      {toast && (
        <div className={`px-4 py-2.5 rounded-lg text-sm ${toast.type === 'success' ? 'bg-green-900/50 text-green-300 border border-green-700' : 'bg-red-900/50 text-red-300 border border-red-700'}`}>
          {toast.msg}
        </div>
      )}

      <button
        type="submit"
        disabled={saving}
        className="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-sm transition-colors"
      >
        {saving ? 'Saving...' : 'Save Mandate'}
      </button>
    </form>
  )
}
