import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { motion } from 'framer-motion'
import { TrendingUp, BarChart2, AlertTriangle, RefreshCw } from 'lucide-react'
import { useStockAnalyze, useStockHistory } from '../../hooks'
import { stockSearchSchema, type StockSearchValues } from '../../lib/schemas'
import { PriceChart } from '../../components/charts/PriceChart'
import { AgentTracePanel } from '../../components/agents/AgentTracePanel'
import { CardSkeleton, ChartSkeleton } from '../../components/ui/LoadingSkeleton'
import { formatCurrency, formatPercent, getChangeColor, getRecommendationBadge, getRecommendationColor } from '../../lib/utils'
import type { StockAnalysis } from '../../types'

const POPULAR = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMZN', 'META']

export function StocksPage() {
  const [analysis, setAnalysis] = useState<StockAnalysis | null>(null)
  const [currentSymbol, setCurrentSymbol] = useState('')

  const analyze = useStockAnalyze()
  const { data: history, isLoading: loadingHistory } = useStockHistory(currentSymbol, !!currentSymbol)

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<StockSearchValues>({
    resolver: zodResolver(stockSearchSchema),
    defaultValues: { period: '1y', include_technical: true, include_fundamental: true, include_news: true, include_sentiment: true },
  })

  const onSubmit = async (data: StockSearchValues) => {
    setCurrentSymbol(data.symbol)
    const result = await analyze.mutateAsync(data)
    setAnalysis(result)
  }

  const handleQuickSearch = (symbol: string) => {
    setValue('symbol', symbol)
    setCurrentSymbol(symbol)
    analyze.mutateAsync({ symbol, period: '1y', include_technical: true, include_fundamental: true, include_news: true, include_sentiment: true })
      .then(setAnalysis)
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Stock Analysis</h1>
        <p className="text-slate-500 text-sm mt-1">AI-powered technical & fundamental analysis</p>
      </div>

      {/* Search */}
      <div className="card p-5">
        <form onSubmit={handleSubmit(onSubmit)} className="flex gap-3 flex-wrap">
          <div className="flex-1 min-w-48">
            <input
              {...register('symbol')}
              placeholder="Enter symbol (e.g. AAPL)"
              className="input w-full"
              style={{ textTransform: 'uppercase' }}
            />
            {errors.symbol && <p className="text-accent-red text-xs mt-1">{errors.symbol.message}</p>}
          </div>
          <select {...register('period')} className="input w-32">
            {['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y'].map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <button type="submit" disabled={analyze.isPending} className="btn-primary flex items-center gap-2">
            {analyze.isPending ? <RefreshCw className="w-4 h-4 animate-spin" /> : <BarChart2 className="w-4 h-4" />}
            {analyze.isPending ? 'Analyzing...' : 'Analyze'}
          </button>
        </form>

        <div className="flex flex-wrap gap-2 mt-3">
          {POPULAR.map((s) => (
            <button
              key={s}
              onClick={() => handleQuickSearch(s)}
              className="text-xs px-3 py-1 bg-surface-700 hover:bg-surface-600 text-slate-300 rounded-full transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {analyze.isPending && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      )}

      {analysis && !analyze.isPending && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
          {/* Price Overview */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card p-4">
              <div className="text-slate-400 text-xs mb-1">Price</div>
              <div className="text-xl font-bold text-slate-100">{formatCurrency(analysis.price.price)}</div>
              <div className={`text-sm ${getChangeColor(analysis.price.change_percent)}`}>
                {formatPercent(analysis.price.change_percent)}
              </div>
            </div>
            <div className="card p-4">
              <div className="text-slate-400 text-xs mb-1">Recommendation</div>
              <div className={`text-lg font-bold ${getRecommendationColor(analysis.recommendation)}`}>
                {analysis.recommendation.replace('_', ' ')}
              </div>
              <div className="text-xs text-slate-500">Confidence: {Math.round(analysis.confidence * 100)}%</div>
            </div>
            {analysis.technical && (
              <>
                <div className="card p-4">
                  <div className="text-slate-400 text-xs mb-1">RSI</div>
                  <div className={`text-xl font-bold ${analysis.technical.rsi > 70 ? 'text-accent-red' : analysis.technical.rsi < 30 ? 'text-accent-green' : 'text-slate-100'}`}>
                    {analysis.technical.rsi?.toFixed(1)}
                  </div>
                  <div className="text-xs text-slate-500">
                    {analysis.technical.rsi > 70 ? 'Overbought' : analysis.technical.rsi < 30 ? 'Oversold' : 'Neutral'}
                  </div>
                </div>
                <div className="card p-4">
                  <div className="text-slate-400 text-xs mb-1">MACD</div>
                  <div className={`text-xl font-bold ${analysis.technical.macd > 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                    {analysis.technical.macd?.toFixed(2)}
                  </div>
                  <div className="text-xs text-slate-500">Signal: {analysis.technical.macd_signal?.toFixed(2)}</div>
                </div>
              </>
            )}
          </div>

          {/* Technical Indicators */}
          {analysis.technical && (
            <div className="card p-5">
              <h3 className="section-title">Technical Indicators</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {[
                  { label: 'SMA 20', value: analysis.technical.sma20 },
                  { label: 'SMA 50', value: analysis.technical.sma50 },
                  { label: 'SMA 200', value: analysis.technical.sma200 },
                  { label: 'BB Upper', value: analysis.technical.bb_upper },
                  { label: 'BB Middle', value: analysis.technical.bb_middle },
                  { label: 'BB Lower', value: analysis.technical.bb_lower },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-surface-700 rounded-lg p-3">
                    <div className="text-xs text-slate-500 mb-1">{label}</div>
                    <div className="text-sm font-semibold text-slate-200">{value ? formatCurrency(value) : '—'}</div>
                  </div>
                ))}
              </div>

              {analysis.technical.signals && analysis.technical.signals.length > 0 && (
                <div className="mt-4">
                  <div className="text-sm text-slate-400 mb-2">Signals</div>
                  <div className="flex flex-wrap gap-2">
                    {analysis.technical.signals.map((sig, i) => (
                      <div key={i} className={`text-xs px-3 py-1.5 rounded-full border ${sig.signal === 'BUY' ? 'badge-green' : sig.signal === 'SELL' ? 'badge-red' : 'badge-yellow'}`}>
                        {sig.indicator}: {sig.signal}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Price Chart */}
          <div className="card p-5">
            <h3 className="section-title">Price History</h3>
            {loadingHistory ? (
              <ChartSkeleton />
            ) : history?.data && history.data.length > 0 ? (
              <PriceChart data={history.data} symbol={currentSymbol} />
            ) : (
              <div className="text-slate-500 text-sm text-center py-8">No chart data available</div>
            )}
          </div>

          {/* Volatility */}
          {analysis.volatility && (
            <div className="card p-5">
              <h3 className="section-title">Volatility & Risk</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {[
                  { label: '30d Volatility', value: `${(analysis.volatility.volatility_30d * 100).toFixed(1)}%` },
                  { label: '90d Volatility', value: `${(analysis.volatility.volatility_90d * 100).toFixed(1)}%` },
                  { label: 'Beta', value: analysis.volatility.beta?.toFixed(2) },
                  { label: 'VaR 95%', value: `${(analysis.volatility.var_95 * 100).toFixed(1)}%` },
                  { label: 'Max Drawdown', value: `${(analysis.volatility.max_drawdown * 100).toFixed(1)}%` },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-surface-700 rounded-lg p-3">
                    <div className="text-xs text-slate-500 mb-1">{label}</div>
                    <div className="text-sm font-semibold text-slate-200">{value ?? '—'}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Summary */}
          {analysis.summary && (
            <div className="card p-5 border border-brand-600/20">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-4 h-4 text-brand-400" />
                <h3 className="text-sm font-semibold text-brand-400">AI Summary</h3>
              </div>
              <p className="text-slate-300 text-sm leading-relaxed">{analysis.summary}</p>
            </div>
          )}

          {/* Agent Trace */}
          {analysis.agents && <AgentTracePanel agents={analysis.agents} />}

          {/* News */}
          {analysis.news && analysis.news.length > 0 && (
            <div className="card p-5">
              <h3 className="section-title">Related News</h3>
              <div className="space-y-3">
                {analysis.news.slice(0, 5).map((item, i) => (
                  <a key={i} href={item.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-start gap-2 p-3 bg-surface-700 rounded-lg hover:bg-surface-600 transition-colors">
                    <div className="flex-1">
                      <div className="text-sm text-slate-200">{item.title}</div>
                      <div className="text-xs text-slate-500 mt-1">{item.source}</div>
                    </div>
                    {item.sentiment && (
                      <span className={`text-xs ${item.sentiment === 'positive' ? 'text-accent-green' : item.sentiment === 'negative' ? 'text-accent-red' : 'text-slate-400'}`}>
                        {item.sentiment}
                      </span>
                    )}
                  </a>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}

      {!analysis && !analyze.isPending && (
        <div className="card p-12 text-center">
          <TrendingUp className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-slate-300 font-medium mb-1">Enter a stock symbol to begin</h3>
          <p className="text-slate-500 text-sm">Get AI-powered analysis with technical indicators, sentiment, and recommendations</p>
        </div>
      )}
    </div>
  )
}
