const S = {
  card: {
    background:   'var(--surface-1)',
    border:       '1px solid var(--border)',
    borderRadius: 20,
    padding:      24,
    boxShadow:    '0 1px 3px rgba(16,24,40,0.06)',
  },
}

function Block({ h = 14, w = '100%', mt = 0, radius = 8 }) {
  return (
    <div
      className="skeleton"
      style={{
        height:       h,
        width:        w,
        background:   'rgba(16, 19, 24, 0.06)',
        borderRadius: radius,
        marginTop:    mt,
        flexShrink:   0,
      }}
    />
  )
}

function Row({ children, gap = 12, mt = 0 }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap, marginTop: mt }}>
      {children}
    </div>
  )
}

function Divider() {
  return <div style={{ height: 1, background: 'var(--border)', margin: '18px 0' }} />
}

export function ScorecardSkeleton() {
  return (
    <div style={S.card}>
      <Row>
        <div style={{ flex: 1 }}>
          <Block h={22} w="55%" />
          <Block h={13} w="32%" mt={8} />
        </div>
        <Block h={26} w={90} radius={6} />
      </Row>
      <Row mt={20} gap={20}>
        <Block h={120} w={120} radius={60} />
        <div style={{ flex: 1 }}>
          <Block h={50} />
          <Block h={50} mt={10} />
        </div>
      </Row>
      <Block h={36} mt={16} radius={10} />
      <Block h={14} w="75%" mt={14} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginTop: 16 }}>
        {Array.from({ length: 6 }).map((_, i) => <Block key={i} h={46} radius={10} />)}
      </div>
    </div>
  )
}

export function ESGSkeleton() {
  return (
    <div style={S.card}>
      <Row>
        <Block h={18} w="40%" />
        <Block h={22} w={88} radius={6} />
      </Row>
      <Block h={38} w="22%" mt={18} />
      {[0, 1, 2].map(i => (
        <div key={i} style={{ marginTop: 16 }}>
          <Row>
            <Block h={12} w="35%" />
            <Block h={12} w="12%" />
          </Row>
          <Block h={4} mt={7} radius={2} />
        </div>
      ))}
    </div>
  )
}

export function MemorySkeleton() {
  return (
    <div style={S.card}>
      <Row>
        <Block h={18} w="42%" />
        <Block h={12} w={100} />
      </Row>
      <Block h={42} w="28%" mt={18} />
      <Block h={13} w="85%" mt={10} />
      <Block h={13} w="68%" mt={6} />
      <Divider />
      {[0, 1, 2].map(i => (
        <div
          key={i}
          style={{
            background:   'rgba(16, 19, 24, 0.03)',
            border:       '1px solid var(--border)',
            borderRadius: 12,
            padding:      14,
            marginTop:    10,
          }}
        >
          <Row gap={8}>
            <Block h={13} w={40} />
            <Block h={13} w={100} />
            <Block h={13} w={70} />
          </Row>
          <Row mt={8} gap={8}>
            <Block h={20} w={64} radius={6} />
            <Block h={12} w={110} />
          </Row>
        </div>
      ))}
    </div>
  )
}

export function ForecastSkeleton() {
  return (
    <div style={S.card}>
      <Row>
        <Block h={18} w="28%" />
        <Block h={12} w="44%" />
      </Row>
      <Block h={36} mt={16} radius={10} />
      {[0, 1, 2, 3].map(i => (
        <div key={i} style={{ marginTop: 14 }}>
          <Row gap={12}>
            <Block h={12} w={90} />
            <Block h={12} w={80} />
            <Block h={12} w={48} />
          </Row>
          <Block h={4} mt={6} radius={2} />
        </div>
      ))}
      <Divider />
      <Row gap={20}>
        <Block h={44} w={76} />
        <div style={{ flex: 1 }}>
          <Block h={12} w="60%" />
          <Block h={12} w="45%" mt={6} />
        </div>
      </Row>
    </div>
  )
}

export function FixSkeleton() {
  return (
    <div style={S.card}>
      <Block h={18} w="30%" />
      <Row mt={20} gap={16} style={{ justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <Block h={44} w={70} />
          <Block h={12} w={80} mt={6} />
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          <Block h={12} w={60} />
          <Block h={1} w="100%" />
        </div>
        <div style={{ textAlign: 'center' }}>
          <Block h={44} w={70} />
          <Block h={12} w={80} mt={6} />
        </div>
      </Row>
      <Block h={60} mt={16} radius={12} />
      {[0, 1, 2].map(i => (
        <div
          key={i}
          style={{
            background:   'rgba(16, 19, 24, 0.03)',
            border:       '1px solid var(--border)',
            borderRadius: 12,
            padding:      14,
            marginTop:    10,
          }}
        >
          <Row gap={8}>
            <Block h={13} w={14} />
            <Block h={13} w={160} />
            <Block h={13} w={60} />
          </Row>
          <Row mt={8} gap={8}>
            <Block h={12} w={50} />
            <Block h={20} w={100} radius={6} />
            <Block h={12} w={60} />
          </Row>
          <Block h={12} w="80%" mt={8} />
        </div>
      ))}
    </div>
  )
}

export function PortfolioSkeleton() {
  return (
    <div style={S.card}>
      <Row>
        <Block h={18} w="32%" />
        <Block h={22} w={88} radius={6} />
      </Row>
      <Block h={13} w="70%" mt={12} />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginTop: 18 }}>
        <div>
          <Block h={12} w={120} />
          <Block h={160} w={160} radius={80} mt={12} style={{ margin: '12px auto 0' }} />
          {[0, 1, 2].map(i => (
            <Row key={i} mt={8}>
              <Block h={12} w="55%" />
              <Block h={12} w="20%" />
            </Row>
          ))}
        </div>
        <div>
          <Block h={12} w={60} />
          {[0, 1, 2, 3, 4].map(i => (
            <Row key={i} mt={10} gap={8}>
              <Block h={8} w={8} radius={4} />
              <Block h={12} w="80%" />
            </Row>
          ))}
          <Block h={12} w={80} mt={18} />
          <Row mt={8} gap={8}>
            <Block h={24} w={50} />
            <Block h={14} w={20} />
            <Block h={24} w={50} />
          </Row>
        </div>
      </div>
    </div>
  )
}

export function BlindSpotSkeleton() {
  return (
    <div style={S.card}>
      <Row>
        <Block h={18} w="38%" />
        <Block h={22} w={100} radius={11} />
      </Row>
      <Block h={13} w="75%" mt={12} />
      {[0, 1, 2].map(i => (
        <div
          key={i}
          style={{
            background:   'rgba(16, 19, 24, 0.03)',
            border:       '1px solid var(--border)',
            borderRadius: 12,
            padding:      14,
            marginTop:    12,
          }}
        >
          <Row gap={8}>
            <Block h={20} w={20} radius={10} />
            <Block h={14} w={120} />
          </Row>
          <Block h={12} w="88%" mt={10} />
          <Block h={36} mt={10} radius={8} />
        </div>
      ))}
    </div>
  )
}
