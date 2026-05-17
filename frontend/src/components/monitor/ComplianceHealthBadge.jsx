import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'

const COLOR_MAP = [
  { min: 75, color: '#12B76A', label: 'COMPLIANT'  },
  { min: 50, color: '#F5A524', label: 'AT RISK'    },
  { min: 25, color: '#EF6820', label: 'DRIFTING'   },
  { min: 0,  color: '#F04438', label: 'IN BREACH'  },
]

function resolve(score) {
  if (score == null) return { color: '#D0D4DC', label: 'NO DATA' }
  return COLOR_MAP.find(c => score >= c.min) ?? COLOR_MAP[COLOR_MAP.length - 1]
}

export default function ComplianceHealthBadge({ score, size = 'lg' }) {
  const { color, label } = resolve(score)
  const dim      = size === 'sm' ? 72 : 160
  const fontSize = size === 'sm' ? 18 : 40
  const data     = [{ value: score ?? 0, fill: color }]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
      <div style={{ width: dim, height: dim, position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%" cy="50%"
            innerRadius="60%" outerRadius="90%"
            startAngle={90} endAngle={-270}
            data={data}
            barSize={size === 'sm' ? 8 : 14}
          >
            <RadialBar
              dataKey="value"
              cornerRadius={4}
              background={{ fill: '#F4F5F7' }}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{
            fontSize, fontWeight: 700, color,
            fontFamily: 'JetBrains Mono, monospace',
            letterSpacing: '-0.03em',
          }}>
            {score ?? '—'}
          </span>
        </div>
      </div>
      <span style={{
        fontSize: 11, fontWeight: 700, letterSpacing: '0.10em',
        color, textTransform: 'uppercase',
      }}>
        {label}
      </span>
    </div>
  )
}
