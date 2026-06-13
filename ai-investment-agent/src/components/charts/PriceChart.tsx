import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ReferenceLine
} from 'recharts'
import { formatDate, formatCurrency } from '../../lib/utils'
import type { HistoryPoint } from '../../types'

interface PriceChartProps {
  data: HistoryPoint[]
  symbol: string
  showSMAs?: boolean
  height?: number
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: {name: string; value: number; color: string}[]; label?: string }) => {
  if (!active || !payload) return null
  return (
    <div className="bg-surface-700 border border-surface-500 rounded-lg p-3 text-xs">
      <p className="text-slate-400 mb-2">{label}</p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
          <span className="text-slate-400">{entry.name}:</span>
          <span className="text-slate-200 font-medium">{formatCurrency(entry.value)}</span>
        </div>
      ))}
    </div>
  )
}

export function PriceChart({ data, symbol, showSMAs = true, height = 320 }: PriceChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    date: formatDate(d.date, true),
    close: Number(d.close.toFixed(2)),
    sma20: d.sma20 ? Number(d.sma20.toFixed(2)) : undefined,
    sma50: d.sma50 ? Number(d.sma50.toFixed(2)) : undefined,
    sma200: d.sma200 ? Number(d.sma200.toFixed(2)) : undefined,
  }))

  const minPrice = Math.min(...data.map((d) => d.low)) * 0.99
  const maxPrice = Math.max(...data.map((d) => d.high)) * 1.01

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 10 }}>
        <defs>
          <linearGradient id={`gradient-${symbol}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.15} />
            <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis
          dataKey="date"
          tick={{ fill: '#64748b', fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          domain={[minPrice, maxPrice]}
          tick={{ fill: '#64748b', fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `$${v.toFixed(0)}`}
          width={60}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }}
          iconType="circle"
          iconSize={8}
        />
        <Area
          type="monotone"
          dataKey="close"
          name="Price"
          stroke="#0ea5e9"
          strokeWidth={1.5}
          fill={`url(#gradient-${symbol})`}
          dot={false}
          activeDot={{ r: 4, fill: '#0ea5e9' }}
        />
        {showSMAs && (
          <>
            <Area type="monotone" dataKey="sma20" name="SMA20" stroke="#8b5cf6" strokeWidth={1} fill="none" dot={false} />
            <Area type="monotone" dataKey="sma50" name="SMA50" stroke="#f59e0b" strokeWidth={1} fill="none" dot={false} />
            <Area type="monotone" dataKey="sma200" name="SMA200" stroke="#ef4444" strokeWidth={1} fill="none" dot={false} />
          </>
        )}
      </AreaChart>
    </ResponsiveContainer>
  )
}
