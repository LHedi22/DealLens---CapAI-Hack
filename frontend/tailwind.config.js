export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:      '#FAFAFB',
        surface: { 1: '#FFFFFF', 2: '#F4F5F7', 3: '#EDEEF2' },
        primary: {
          DEFAULT: '#6E56CF',
          soft:    '#8B7CFF',
          glow:    '#B8A9FF',
        },
        gold: '#6E56CF',
        score: {
          green:  '#12B76A',
          amber:  '#F5A524',
          orange: '#EF6820',
          red:    '#F04438',
        },
        tx:     { 1: '#111318', 2: '#3D4754', 3: '#64748B' },
        border: '#E7E9EE',
        // Legacy aliases
        'score-green':  '#12B76A',
        'score-amber':  '#F5A524',
        'score-orange': '#EF6820',
        'score-red':    '#F04438',
        'bg-primary':   '#FAFAFB',
        'bg-card':      '#FFFFFF',
        'text-primary': '#111318',
        'text-muted':   '#3D4754',
        accent:         '#6E56CF',
      },
      fontFamily: {
        sans:    ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono:    ['JetBrains Mono', 'monospace'],
        display: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
      },
      borderColor: {
        DEFAULT: '#E7E9EE',
      },
      boxShadow: {
        card:          '0 1px 3px rgba(16,24,40,0.06), 0 4px 16px rgba(16,24,40,0.04)',
        'card-hover':  '0 4px 20px rgba(16,24,40,0.10), 0 2px 6px rgba(16,24,40,0.06)',
        'purple-glow': '0 0 0 3px rgba(110,86,207,0.12)',
      },
    },
  },
  plugins: [],
}
