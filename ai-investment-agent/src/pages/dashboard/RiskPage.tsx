import { useState } from 'react'
import { motion } from 'framer-motion'
import { Shield, Plus, X, RefreshCw, AlertTriangle } from 'lucide-react'
import { useRiskAnalyze, usePortfolios } from '../../hooks'
import { RiskBarChart, Gauge } from '../../components/charts/AllocationChart'
import { getRiskLevelColor } from '../../lib/utils'
import type { RiskAnalysis } from '../../types'

export function RiskPage() {
  const [symbols, setSymbols] = useState<string[]>(['AAPL', 'MSFT', 'GOOGL'])
  const [inputVal, setInputVal] = useState('')
  const [analysis, setAnalysis] = useState<RiskAnalysis | null>(null)
  const { data: portfolios } = usePortfolios()
  const riskAnalyze = useRiskAnalyze()

  const addSymbol = () => {
    const s = inputVal.trim().toUpperCase()
    if (s && !symbols.includes(s)) {
      setSymbols([...symbols, s])
      setInputVal('')
    }
  }

  const removeSymbol = (s: string) => setSymbols(symbols.filter((x) => x !== s))

  const runAnalysis = async () => {
    const result = await riskAnalyze.mutateAsync({ symbols })
    setAnalysis(result)
  }

  const runPortfolioAnalysis = async (portfolioId: string) => {
    const result = await riskAnalyze.mutateAsync({ portfolio_id: portfolioId })
    setAnalysis(result)
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Risk Analysis</h1>
        <p className="text-slate-500 text-sm mt-1">Portfolio risk metrics and diversification analysis</p>
      </div>

      {/* Input */}
      <div className="card p-5 space-y-4">
        <div>
          <label className="label">Symbols to analyze</label>
          <div className="flex gap-2">
            <input
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && addSymbol()}
              placeholder="Add symbol (e.g. NVDA)"
              className="input flex-1"
            />
            <button onClick={addSymbol} className="btn-secondary flex items-center gap-1">
              <Plus className="w-4 h-4" /> Add
            </button>
          </div>
          <div className="flex flex-wrap gap-2 mt-2">
            {symbols.map((s) => (
              <span key={s} className="flex items-center gap-1 bg-surface-700 text-slate-300 text-xs px-2.5 py-1 rounded-full">
                {s}
                <button onClick={() => removeSymbol(s)} className="text-slate-500 hover:text-accent-red ml-1">
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>

        <div className="flex gap-3 flex-wrap">
          <button
            onClick={runAnalysis}
            disabled={riskAnalyze.isPending || symbols.length === 0}
            className="btn-primary flex items-center gap-2"
          >
            {riskAnalyze.isPending ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
            Analyze Symbols
          </button>
          {portfolios && portfolios.map((p) => (
            <button
              key={p.id}
              onClick={() => runPortfolioAnalysis(p.id)}
              disabled={riskAnalyze.isPending}
              className="btn-secondary text-sm"
            >
              Analyze "{p.name}"
            </button>
          ))}
        </div>
      </div>

      {analysis && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
          {/* Top metrics */}
          <div className="card p-5">
            <div className="flex items-center gap-3 mb-5">
              <div className={`text-3xl font-bold ${getRiskLevelColor(analysis.risk_level)}`}>
                {analysis.risk_score.toFixed(1)}
              </div>
              <div>
                <div className={`text-lg font-semibold ${getRiskLevelColor(analysis.risk_level)}`}>
                  {analysis.risk_level.replace('_', ' ')} Risk
                </div>
                <div className="text-sm text-slate-500">Overall portfolio risk score</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-8 justify-center">
              <Gauge value={analysis.portfolio_volatility * 100} max={50} label="Volatility %" color="#ef4444" />
              <Gauge value={analysis.portfolio_beta} max={2} label="Beta" color="#f59e0b" />
              <Gauge value={analysis.sharpe_ratio} max={3} label="Sharpe Ratio" color="#10b981" />
              <Gauge value={analysis.diversification_score} max={100} label="Diversification" color="#0ea5e9" />
            </div>
          </div>

          {/* Detail metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Portfolio Beta', value: analysis.portfolio_beta.toFixed(2) },
              { label: 'Volatility', value: `${(analysis.portfolio_volatility * 100).toFixed(1)}%` },
              { label: 'Sharpe Ratio', value: analysis.sharpe_ratio.toFixed(2) },
              { label: 'Max Drawdown', value: `${(analysis.max_drawdown * 100).toFixed(1)}%` },
              { label: 'VaR 95%', value: `${(analysis.var_95 * 100).toFixed(1)}%` },
              { label: 'Diversification', value: `${analysis.diversification_score.toFixed(0)}/100` },
            ].map(({ label, value }) => (
              <div key={label} className="card p-4">
                <div className="text-xs text-slate-500 mb-1">{label}</div>
                <div className="text-lg font-bold text-slate-100">{value}</div>
              </div>
            ))}
          </div>

          {/* Per-symbol chart */}
          {analysis.symbols && analysis.symbols.length > 0 && (
            <div className="card p-5">
              <h3 className="section-title">Per-Symbol Risk</h3>
              <RiskBarChart
                data={analysis.symbols.map((s) => ({
                  symbol: s.symbol,
                  volatility: s.volatility,
                  contribution: s.contribution,
                }))}
              />
              <div className="overflow-x-auto mt-4">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-500 text-xs border-b border-surface-600">
                      <th className="text-left pb-2">Symbol</th>
                      <th className="text-right pb-2">Weight</th>
                      <th className="text-right pb-2">Volatility</th>
                      <th className="text-right pb-2">Beta</th>
                      <th className="text-right pb-2">VaR 95%</th>
                      <th className="text-right pb-2">Risk Contribution</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-700">
                    {analysis.symbols.map((s) => (
                      <tr key={s.symbol} className="hover:bg-surface-700/50">
                        <td className="py-2 font-medium text-slate-200">{s.symbol}</td>
                        <td className="py-2 text-right text-slate-400">{(s.weight * 100).toFixed(1)}%</td>
                        <td className="py-2 text-right text-slate-400">{(s.volatility * 100).toFixed(1)}%</td>
                        <td className="py-2 text-right text-slate-400">{s.beta?.toFixed(2) ?? '—'}</td>
                        <td className="py-2 text-right text-slate-400">{(s.var_95 * 100).toFixed(1)}%</td>
                        <td className="py-2 text-right text-slate-400">{(s.contribution * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Recommendations */}
          {analysis.recommendations && analysis.recommendations.length > 0 && (
            <div className="card p-5">
              <h3 className="section-title flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-accent-yellow" /> Recommendations
              </h3>
              <ul className="space-y-2">
                {analysis.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                    <span className="text-accent-yellow mt-0.5">•</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}

      {!analysis && !riskAnalyze.isPending && (
        <div className="card p-12 text-center">
          <Shield className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-slate-300 font-medium mb-1">Add symbols and run analysis</h3>
          <p className="text-slate-500 text-sm">Get comprehensive risk metrics including VaR, beta, Sharpe ratio and diversification score</p>
        </div>
      )}
    </div>
  )
}
