import { useState } from 'react'
import { motion } from 'framer-motion'
import { Newspaper, Search, Filter } from 'lucide-react'
import { useMarketNews, useSymbolNews } from '../../hooks'
import { NewsCard } from '../../components/ui/NewsCard'
import { CardSkeleton } from '../../components/ui/LoadingSkeleton'

const SENTIMENTS = ['all', 'positive', 'negative', 'neutral']
const POPULAR = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMZN']

export function NewsPage() {
  const [symbolFilter, setSymbolFilter] = useState('')
  const [activeSymbol, setActiveSymbol] = useState('')
  const [sentimentFilter, setSentimentFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')

  const { data: marketNews, isLoading: loadingMarket } = useMarketNews()
  const { data: symbolNews, isLoading: loadingSymbol } = useSymbolNews(activeSymbol, !!activeSymbol)

  const rawNews = activeSymbol ? symbolNews : marketNews
  const isLoading = activeSymbol ? loadingSymbol : loadingMarket

  const filteredNews = rawNews?.filter((item) => {
    if (sentimentFilter !== 'all' && item.sentiment !== sentimentFilter) return false
    if (searchTerm && !item.title.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  const handleSymbolSearch = () => {
    const s = symbolFilter.trim().toUpperCase()
    if (s) setActiveSymbol(s)
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Market News</h1>
        <p className="text-slate-500 text-sm mt-1">AI-analyzed financial news with sentiment scoring</p>
      </div>

      {/* Filters */}
      <div className="card p-5 space-y-4">
        <div className="flex gap-3 flex-wrap">
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search news..."
              className="input w-full pl-9"
            />
          </div>
          <div className="flex gap-2 items-center">
            <input
              value={symbolFilter}
              onChange={(e) => setSymbolFilter(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && handleSymbolSearch()}
              placeholder="Filter by symbol"
              className="input w-36"
            />
            <button onClick={handleSymbolSearch} className="btn-secondary">Go</button>
            {activeSymbol && (
              <button onClick={() => { setActiveSymbol(''); setSymbolFilter('') }} className="btn-ghost text-sm">
                Clear
              </button>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="w-4 h-4 text-slate-500" />
          <span className="text-xs text-slate-500">Sentiment:</span>
          {SENTIMENTS.map((s) => (
            <button
              key={s}
              onClick={() => setSentimentFilter(s)}
              className={`text-xs px-3 py-1 rounded-full transition-colors ${
                sentimentFilter === s
                  ? 'bg-brand-600 text-white'
                  : 'bg-surface-700 text-slate-400 hover:text-slate-200'
              }`}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
          <span className="text-slate-600 mx-1">|</span>
          <span className="text-xs text-slate-500">Quick:</span>
          {POPULAR.map((s) => (
            <button
              key={s}
              onClick={() => { setActiveSymbol(s); setSymbolFilter(s) }}
              className={`text-xs px-3 py-1 rounded-full transition-colors ${
                activeSymbol === s
                  ? 'bg-surface-500 text-slate-200'
                  : 'bg-surface-700 text-slate-500 hover:text-slate-300'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* News count */}
      {!isLoading && filteredNews && (
        <div className="flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-slate-500" />
          <span className="text-sm text-slate-500">
            {filteredNews.length} articles
            {activeSymbol && ` for ${activeSymbol}`}
          </span>
        </div>
      )}

      {/* News Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : filteredNews && filteredNews.length > 0 ? (
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 gap-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {filteredNews.map((item, i) => (
            <NewsCard key={i} item={item} />
          ))}
        </motion.div>
      ) : (
        <div className="card p-12 text-center">
          <Newspaper className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">No news found</p>
          <p className="text-slate-600 text-sm mt-1">Try adjusting your filters</p>
        </div>
      )}
    </div>
  )
}
