import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line } from 'recharts'
import { formatCurrency, formatPercent } from '../../lib/utils'

const COLORS = ['#0ea5e9', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#84cc16']

// ─── ALLOCATION PIE CHART ─────────────────────────────────────
interface AllocationChartProps {
  data: Record<string, number>
  title?: string
  height?: number
}

export function AllocationChart({ data, title = 'Allocation', height = 280 }: AllocationChartProps) {
  const chartData = Object.entries(data).map(([name, value]) => ({ name, value: Number((value * 100).toFixed(1)) }))

  return (
    <div>
      {title && <div className="text-sm text-slate-400 mb-2">{title}</div>}
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={90}
            paddingAngle={3}
            dataKey="value"
          >
            {chartData.map((_, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(v: number) => [`${v}%`, '']}
            contentStyle={{ background: '#1a2235', border: '1px solid #243044', borderRadius: '8px', fontSize: '12px' }}
          />
          <Legend
            formatter={(v) => <span style={{ color: '#94a3b8', fontSize: '12px' }}>{v}</span>}
            iconType="circle"
            iconSize={8}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

// ─── PERFORMANCE LINE CHART ───────────────────────────────────
interface PerformanceChartProps {
  data: { date: string; value: number }[]
  height?: number
}

export function PerformanceChart({ data, height = 220 }: PerformanceChartProps) {
  const isPositive = data.length > 1 && data[data.length - 1].value >= data[0].value
  const color = isPositive ? '#10b981' : '#ef4444'

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
        <defs>
          <linearGradient id="perfGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.2} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} />
        <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
        <Tooltip
          formatter={(v: number) => [formatCurrency(v), 'Value']}
          contentStyle={{ background: '#1a2235', border: '1px solid #243044', borderRadius: '8px', fontSize: '12px' }}
        />
        <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}

// ─── RISK BAR CHART ───────────────────────────────────────────
interface RiskBarProps {
  data: { symbol: string; volatility: number; contribution: number }[]
  height?: number
}

export function RiskBarChart({ data, height = 240 }: RiskBarProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="symbol" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip
          formatter={(v: number) => [`${(v * 100).toFixed(1)}%`, '']}
          contentStyle={{ background: '#1a2235', border: '1px solid #243044', borderRadius: '8px', fontSize: '12px' }}
        />
        <Bar dataKey="volatility" name="Volatility" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
        <Bar dataKey="contribution" name="Risk Contribution" fill="#ef4444" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

// ─── GAUGE COMPONENT ──────────────────────────────────────────
interface GaugeProps {
  value: number
  max?: number
  label: string
  color?: string
}

export function Gauge({ value, max = 100, label, color = '#0ea5e9' }: GaugeProps) {
  const pct = Math.min((value / max) * 100, 100)
  const r = 40
  const circ = 2 * Math.PI * r
  const strokeDash = (pct / 100) * circ * 0.75
  const strokeOffset = circ * 0.125

  return (
    <div className="flex flex-col items-center">
      <svg width="100" height="70" viewBox="0 0 100 70">
        <circle cx="50" cy="55" r={r} fill="none" stroke="#1a2235" strokeWidth="8"
          strokeDasharray={`${circ * 0.75} ${circ}`}
          strokeDashoffset={-strokeOffset}
          strokeLinecap="round"
        />
        <circle cx="50" cy="55" r={r} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={`${strokeDash} ${circ}`}
          strokeDashoffset={-strokeOffset}
          strokeLinecap="round"
        />
        <text x="50" y="52" textAnchor="middle" fill="#e2e8f0" fontSize="14" fontWeight="bold">
          {value.toFixed(1)}
        </text>
      </svg>
      <span className="text-xs text-slate-500 mt-1">{label}</span>
    </div>
  )
}
