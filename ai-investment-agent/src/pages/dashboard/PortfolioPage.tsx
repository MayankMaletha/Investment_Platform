import { useState } from 'react'
import { motion } from 'framer-motion'
import { Plus, Briefcase, Trash2, ChevronRight } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { usePortfolios, useCreatePortfolio, useDeletePortfolio, usePortfolio, usePortfolioPerformance, useBuyAsset, useSellAsset } from '../../hooks'
import { portfolioCreateSchema, type PortfolioCreateValues } from '../../lib/schemas'
import { AllocationChart, PerformanceChart } from '../../components/charts/AllocationChart'
import { CardSkeleton } from '../../components/ui/LoadingSkeleton'
import { formatCurrency, formatPercent, getChangeColor } from '../../lib/utils'

export function PortfolioPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)

  const { data: portfolios, isLoading } = usePortfolios()
  const { data: selected } = usePortfolio(selectedId || '', !!selectedId)
  const { data: performance } = usePortfolioPerformance(selectedId || '', !!selectedId)
  const createPortfolio = useCreatePortfolio()
  const deletePortfolio = useDeletePortfolio()

  // Transaction form states
  const [showTxForm, setShowTxForm] = useState(false)
  const [txType, setTxType] = useState<'buy' | 'sell'>('buy')
  const [txSymbol, setTxSymbol] = useState('')
  const [txAssetType, setTxAssetType] = useState('stock')
  const [txQuantity, setTxQuantity] = useState('')
  const [txPrice, setTxPrice] = useState('')
  const [txNotes, setTxNotes] = useState('')

  const buyAsset = useBuyAsset(selectedId || '')
  const sellAsset = useSellAsset(selectedId || '')

  const handleTxSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!txSymbol || !txQuantity || !txPrice) return

    const payload = {
      symbol: txSymbol.toUpperCase(),
      asset_type: txAssetType,
      quantity: parseFloat(txQuantity),
      price: parseFloat(txPrice),
      notes: txNotes || undefined
    }

    if (txType === 'buy') {
      await buyAsset.mutateAsync(payload)
    } else {
      await sellAsset.mutateAsync(payload)
    }

    // Reset state
    setTxSymbol('')
    setTxQuantity('')
    setTxPrice('')
    setTxNotes('')
    setShowTxForm(false)
  }

  const { register, handleSubmit, reset, formState: { errors } } = useForm<PortfolioCreateValues>({
    resolver: zodResolver(portfolioCreateSchema),
  })

  const onCreateSubmit = async (data: PortfolioCreateValues) => {
    await createPortfolio.mutateAsync(data)
    reset()
    setShowCreate(false)
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Portfolio</h1>
          <p className="text-slate-500 text-sm mt-1">Manage your investment portfolios</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Portfolio
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="card p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Create Portfolio</h3>
          <form onSubmit={handleSubmit(onCreateSubmit)} className="flex gap-3 flex-wrap">
            <div className="flex-1 min-w-40">
              <input {...register('name')} placeholder="Portfolio name" className="input w-full" />
              {errors.name && <p className="text-accent-red text-xs mt-1">{errors.name.message}</p>}
            </div>
            <input {...register('description')} placeholder="Description (optional)" className="input flex-1 min-w-40" />
            <button type="submit" disabled={createPortfolio.isPending} className="btn-primary">
              {createPortfolio.isPending ? 'Creating...' : 'Create'}
            </button>
            <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
          </form>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Portfolio List */}
        <div className="space-y-3">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => <CardSkeleton key={i} />)
          ) : portfolios && portfolios.length > 0 ? (
            portfolios.map((p) => (
              <div
                key={p.id}
                onClick={() => setSelectedId(p.id)}
                className={`card p-4 cursor-pointer transition-all ${selectedId === p.id ? 'border-brand-500' : 'hover:border-surface-400'}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Briefcase className="w-4 h-4 text-brand-400" />
                    <div>
                      <div className="font-medium text-slate-200 text-sm">{p.name}</div>
                      <div className="text-xs text-slate-500">{p.holdings.length} holdings</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={(e) => { e.stopPropagation(); deletePortfolio.mutate(p.id) }}
                      className="p-1 text-slate-600 hover:text-accent-red transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                    <ChevronRight className="w-4 h-4 text-slate-600" />
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-surface-600">
                  <div className="text-lg font-bold text-slate-100">{formatCurrency(p.total_value, 'USD', true)}</div>
                  {p.total_gain_loss_percent !== undefined && (
                    <div className={`text-sm ${getChangeColor(p.total_gain_loss_percent)}`}>
                      {formatPercent(p.total_gain_loss_percent)}
                    </div>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="card p-8 text-center">
              <Briefcase className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-slate-500 text-sm">No portfolios yet</p>
            </div>
          )}
        </div>

        {/* Portfolio Detail */}
        <div className="lg:col-span-2 space-y-4">
          {selected ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
              {/* Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: 'Total Value', value: formatCurrency(selected.total_value, 'USD', true) },
                  { label: 'Total P&L', value: formatCurrency(selected.total_gain_loss || 0, 'USD', true) },
                  { label: 'Beta', value: selected.beta?.toFixed(2) || '—' },
                  { label: 'Sharpe Ratio', value: selected.sharpe_ratio?.toFixed(2) || '—' },
                  { label: 'Volatility', value: selected.volatility ? `${(selected.volatility * 100).toFixed(1)}%` : '—' },
                  { label: 'Risk Score', value: selected.risk_score?.toFixed(1) || '—' },
                  { label: 'Diversification', value: selected.diversification_score?.toFixed(1) || '—' },
                  { label: 'Holdings', value: String(selected.holdings.length) },
                ].map(({ label, value }) => (
                  <div key={label} className="card p-3">
                    <div className="text-xs text-slate-500 mb-1">{label}</div>
                    <div className="text-sm font-semibold text-slate-200">{value}</div>
                  </div>
                ))}
              </div>

              {/* Allocation & Performance */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {selected.sector_allocation && Object.keys(selected.sector_allocation).length > 0 && (
                  <div className="card p-4">
                    <AllocationChart data={selected.sector_allocation} title="Sector Allocation" height={220} />
                  </div>
                )}
                {performance && Array.isArray(performance) && performance.length > 0 && (
                  <div className="card p-4">
                    <div className="text-sm text-slate-400 mb-2">Performance</div>
                    <PerformanceChart data={performance} />
                  </div>
                )}
              </div>

              {/* Holdings Card */}
              <div className="card p-5">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-bold text-slate-100">Holdings</h3>
                  <button
                    onClick={() => setShowTxForm(!showTxForm)}
                    className="text-xs px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-slate-100 font-medium rounded-lg transition-colors flex items-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" /> Add Transaction
                  </button>
                </div>

                {showTxForm && (
                  <form onSubmit={handleTxSubmit} className="mb-6 p-4 bg-surface-700 rounded-lg space-y-4">
                    <h4 className="text-sm font-semibold text-slate-200">New Transaction</h4>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                      <div>
                        <label className="label text-xs">Type</label>
                        <select
                          value={txType}
                          onChange={(e) => setTxType(e.target.value as 'buy' | 'sell')}
                          className="input w-full text-xs"
                        >
                          <option value="buy">BUY</option>
                          <option value="sell">SELL</option>
                        </select>
                      </div>
                      <div>
                        <label className="label text-xs">Symbol</label>
                        <input
                          type="text"
                          required
                          placeholder="e.g. AAPL"
                          value={txSymbol}
                          onChange={(e) => setTxSymbol(e.target.value)}
                          className="input w-full text-xs"
                          style={{ textTransform: 'uppercase' }}
                        />
                      </div>
                      <div>
                        <label className="label text-xs">Asset Type</label>
                        <select
                          value={txAssetType}
                          onChange={(e) => setTxAssetType(e.target.value)}
                          className="input w-full text-xs"
                        >
                          <option value="stock">Stock</option>
                          <option value="crypto">Crypto</option>
                          <option value="etf">ETF</option>
                          <option value="bond">Bond</option>
                        </select>
                      </div>
                      <div>
                        <label className="label text-xs">Quantity</label>
                        <input
                          type="number"
                          required
                          step="any"
                          min="0.00000001"
                          placeholder="0.0"
                          value={txQuantity}
                          onChange={(e) => setTxQuantity(e.target.value)}
                          className="input w-full text-xs"
                        />
                      </div>
                      <div>
                        <label className="label text-xs">Price (USD)</label>
                        <input
                          type="number"
                          required
                          step="any"
                          min="0.01"
                          placeholder="0.00"
                          value={txPrice}
                          onChange={(e) => setTxPrice(e.target.value)}
                          className="input w-full text-xs"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="label text-xs">Notes (optional)</label>
                      <input
                        type="text"
                        placeholder="Transaction notes..."
                        value={txNotes}
                        onChange={(e) => setTxNotes(e.target.value)}
                        className="input w-full text-xs"
                      />
                    </div>
                    <div className="flex gap-2 justify-end">
                      <button
                        type="button"
                        onClick={() => setShowTxForm(false)}
                        className="px-3 py-1.5 text-xs bg-surface-600 hover:bg-surface-500 text-slate-300 rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={buyAsset.isPending || sellAsset.isPending}
                        className="px-3 py-1.5 text-xs bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-slate-100 font-medium rounded-lg transition-colors"
                      >
                        {buyAsset.isPending || sellAsset.isPending ? 'Submitting...' : 'Submit'}
                      </button>
                    </div>
                  </form>
                )}

                {selected.holdings.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-slate-500 text-xs border-b border-surface-600">
                          <th className="text-left pb-3">Symbol</th>
                          <th className="text-right pb-3">Qty</th>
                          <th className="text-right pb-3">Avg Cost</th>
                          <th className="text-right pb-3">Current</th>
                          <th className="text-right pb-3">Value</th>
                          <th className="text-right pb-3">P&L</th>
                          <th className="text-right pb-3">P&L %</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-surface-700">
                        {selected.holdings.map((h) => (
                          <tr key={h.symbol} className="hover:bg-surface-700/50">
                            <td className="py-2.5">
                              <div className="font-medium text-slate-200">{h.symbol}</div>
                              {h.sector && <div className="text-xs text-slate-500">{h.sector}</div>}
                            </td>
                            <td className="py-2.5 text-right text-slate-300">{h.quantity}</td>
                            <td className="py-2.5 text-right text-slate-400">{formatCurrency(h.average_cost)}</td>
                            <td className="py-2.5 text-right text-slate-300">{h.current_price ? formatCurrency(h.current_price) : '—'}</td>
                            <td className="py-2.5 text-right text-slate-200">{h.current_value ? formatCurrency(h.current_value, 'USD', true) : '—'}</td>
                            <td className={`py-2.5 text-right ${h.gain_loss !== undefined ? getChangeColor(h.gain_loss) : 'text-slate-400'}`}>
                              {h.gain_loss !== undefined ? formatCurrency(h.gain_loss, 'USD', true) : '—'}
                            </td>
                            <td className={`py-2.5 text-right ${h.gain_loss_percent !== undefined ? getChangeColor(h.gain_loss_percent) : 'text-slate-400'}`}>
                              {h.gain_loss_percent !== undefined ? formatPercent(h.gain_loss_percent) : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-slate-500 text-sm py-4 text-center">No holdings in this portfolio yet. Use the "Add Transaction" button above to buy assets.</p>
                )}
              </div>
            </motion.div>
          ) : (
            <div className="card p-12 text-center">
              <Briefcase className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">Select a portfolio to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
