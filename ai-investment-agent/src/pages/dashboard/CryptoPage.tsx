import { useState } from 'react'
import { motion } from 'framer-motion'
import { Bitcoin, RefreshCw, Search } from 'lucide-react'
import { useCryptoTop, useCryptoAnalyze } from '../../hooks'
import { AgentTracePanel } from '../../components/agents/AgentTracePanel'
import { CardSkeleton } from '../../components/ui/LoadingSkeleton'
import { formatCurrency, formatPercent, getChangeColor, getRecommendationColor } from '../../lib/utils'
import type { CryptoAnalysis } from '../../types'
import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts'

export function CryptoPage() {
  const [analysis, setAnalysis] = useState<CryptoAnalysis | null>(null)
  const [searchSymbol, setSearchSymbol] = useState('')
  const { data: topCoins, isLoading } = useCryptoTop()
  const analyze = useCryptoAnalyze()

  const handleAnalyze = async (symbol: string) => {
    const result = await analyze.mutateAsync({ symbol, vs_currency: 'usd', days: 30, include_sentiment: true })
    setAnalysis(result)
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Crypto Analysis</h1>
        <p className="text-slate-500 text-sm mt-1">Real-time crypto prices with AI sentiment analysis</p>
      </div>

      {/* Search */}
      <div className="card p-5">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              value={searchSymbol}
              onChange={(e) => setSearchSymbol(e.target.value)}
              placeholder="Enter crypto ID (e.g. bitcoin, ethereum)"
              className="input w-full pl-9"
              onKeyDown={(e) => e.key === 'Enter' && searchSymbol && handleAnalyze(searchSymbol)}
            />
          </div>
          <button
            onClick={() => searchSymbol && handleAnalyze(searchSymbol)}
            disabled={analyze.isPending || !searchSymbol}
            className="btn-primary flex items-center gap-2"
          >
            {analyze.isPending ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Bitcoin className="w-4 h-4" />}
            Analyze
          </button>
        </div>
      </div>

      {/* Analysis Result */}
      {analysis && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card p-4">
              <div className="text-slate-400 text-xs mb-1">Price (USD)</div>
              <div className="text-xl font-bold text-slate-100">{formatCurrency(analysis.price.current_price)}</div>
              <div className={`text-sm ${getChangeColor(analysis.price.price_change_percentage_24h)}`}>
                {formatPercent(analysis.price.price_change_percentage_24h)} 24h
              </div>
            </div>
            <div className="card p-4">
              <div className="text-slate-400 text-xs mb-1">Recommendation</div>
              <div className={`text-lg font-bold ${getRecommendationColor(analysis.recommendation)}`}>
                {analysis.recommendation}
              </div>
              <div className="text-xs text-slate-500">Confidence: {Math.round(analysis.confidence * 100)}%</div>
            </div>
            <div className="card p-4">
              <div className="text-slate-400 text-xs mb-1">Trend</div>
              <div className="text-lg font-bold text-slate-100">{analysis.trend}</div>
            </div>
            <div className="card p-4">
              <div className="text-slate-400 text-xs mb-1">Sentiment Score</div>
              <div className={`text-xl font-bold ${analysis.sentiment_score > 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                {analysis.sentiment_score?.toFixed(2)}
              </div>
            </div>
          </div>

          {/* Price Chart */}
          {analysis.price_history && analysis.price_history.length > 0 && (
            <div className="card p-5">
              <h3 className="section-title">30-Day Price</h3>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={analysis.price_history}>
                  <Line type="monotone" dataKey="price" stroke="#0ea5e9" strokeWidth={1.5} dot={false} />
                  <Tooltip
                    formatter={(v: number) => [formatCurrency(v), 'Price']}
                    contentStyle={{ background: '#1a2235', border: '1px solid #243044', borderRadius: '8px', fontSize: '12px' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {analysis.summary && (
            <div className="card p-5 border border-brand-600/20">
              <p className="text-slate-300 text-sm leading-relaxed">{analysis.summary}</p>
            </div>
          )}

          <AgentTracePanel agents={analysis.agents} />
        </motion.div>
      )}

      {/* Top Coins Table */}
      <div className="card p-5">
        <h2 className="section-title">Top 20 by Market Cap</h2>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 8 }).map((_, i) => <CardSkeleton key={i} />)}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-500 text-xs border-b border-surface-600">
                  <th className="text-left pb-3 pr-4">#</th>
                  <th className="text-left pb-3 pr-4">Coin</th>
                  <th className="text-right pb-3 pr-4">Price</th>
                  <th className="text-right pb-3 pr-4">24h Change</th>
                  <th className="text-right pb-3 pr-4">Market Cap</th>
                  <th className="text-right pb-3">Volume</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-700">
                {topCoins?.map((coin) => (
                  <tr
                    key={coin.id}
                    className="hover:bg-surface-700/50 cursor-pointer transition-colors"
                    onClick={() => handleAnalyze(coin.id)}
                  >
                    <td className="py-3 pr-4 text-slate-500">{coin.rank}</td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2">
                        <img src={coin.image} alt={coin.name} className="w-6 h-6 rounded-full" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }} />
                        <div>
                          <div className="font-medium text-slate-200">{coin.name}</div>
                          <div className="text-xs text-slate-500">{coin.symbol.toUpperCase()}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-right font-medium text-slate-200">{formatCurrency(coin.current_price)}</td>
                    <td className={`py-3 pr-4 text-right ${getChangeColor(coin.price_change_percentage_24h)}`}>
                      {formatPercent(coin.price_change_percentage_24h)}
                    </td>
                    <td className="py-3 pr-4 text-right text-slate-400">{formatCurrency(coin.market_cap, 'USD', true)}</td>
                    <td className="py-3 text-right text-slate-400">{formatCurrency(coin.volume_24h, 'USD', true)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
