import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, DollarSign, Shield, Briefcase, Activity } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { usePortfolios, useCryptoTop, useMarketNews, useChatSessions } from '../../hooks'
import { DashboardCard } from '../../components/ui/DashboardCard'
import { NewsCard } from '../../components/ui/NewsCard'
import { CardSkeleton } from '../../components/ui/LoadingSkeleton'
import { formatCurrency, formatPercent, getChangeColor } from '../../lib/utils'
import { useAuthStore } from '../../stores/auth-store'

const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
}

export function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const { data: portfolios, isLoading: loadingPortfolios } = usePortfolios()
  const { data: cryptoTop, isLoading: loadingCrypto } = useCryptoTop()
  const { data: news, isLoading: loadingNews } = useMarketNews()
  const { data: sessions } = useChatSessions()

  const totalValue = portfolios?.reduce((sum, p) => sum + (p.total_value || 0), 0) || 0
  const totalGain = portfolios?.reduce((sum, p) => sum + (p.total_gain_loss || 0), 0) || 0
  const avgRisk = portfolios?.length
    ? portfolios.reduce((sum, p) => sum + (p.risk_score || 0), 0) / portfolios.length
    : 0

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <motion.div {...fadeUp} transition={{ duration: 0.3 }}>
        <h1 className="text-2xl font-bold text-slate-100">
          Good morning, {user?.full_name?.split(' ')[0] || 'Investor'}
        </h1>
        <p className="text-slate-500 text-sm mt-1">Here's your investment overview</p>
      </motion.div>

      {/* KPI Cards */}
      <motion.div
        className="grid grid-cols-2 lg:grid-cols-4 gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        {loadingPortfolios ? (
          Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)
        ) : (
          <>
            <DashboardCard
              title="Total Portfolio Value"
              value={formatCurrency(totalValue, 'USD', true)}
              icon={<DollarSign className="w-4 h-4" />}
              trend={portfolios?.[0]?.total_gain_loss_percent}
              subtitle="across all portfolios"
            />
            <DashboardCard
              title="Total P&L"
              value={formatCurrency(totalGain, 'USD', true)}
              icon={totalGain >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              subtitle="unrealized gain/loss"
              className={totalGain >= 0 ? 'border-accent-green/20' : 'border-accent-red/20'}
            />
            <DashboardCard
              title="Portfolios"
              value={String(portfolios?.length || 0)}
              icon={<Briefcase className="w-4 h-4" />}
              subtitle="active portfolios"
            />
            <DashboardCard
              title="Avg. Risk Score"
              value={avgRisk ? avgRisk.toFixed(1) : '—'}
              icon={<Shield className="w-4 h-4" />}
              subtitle="risk-adjusted"
            />
          </>
        )}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Crypto */}
        <motion.div
          className="lg:col-span-1"
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="section-title mb-0">Top Crypto</h2>
              <Link to="/dashboard/crypto" className="text-xs text-brand-400 hover:text-brand-300">View all →</Link>
            </div>
            {loadingCrypto ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-3 animate-pulse">
                    <div className="w-8 h-8 bg-surface-600 rounded-full" />
                    <div className="flex-1 space-y-1">
                      <div className="h-3 bg-surface-600 rounded w-1/2" />
                      <div className="h-2 bg-surface-600 rounded w-1/3" />
                    </div>
                    <div className="h-3 bg-surface-600 rounded w-16" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {cryptoTop?.slice(0, 7).map((coin) => (
                  <div key={coin.id} className="flex items-center gap-3">
                    <img src={coin.image} alt={coin.name} className="w-7 h-7 rounded-full" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }} />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-slate-200 truncate">{coin.name}</div>
                      <div className="text-xs text-slate-500">{coin.symbol.toUpperCase()}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-slate-200">{formatCurrency(coin.current_price)}</div>
                      <div className={`text-xs ${getChangeColor(coin.price_change_percentage_24h)}`}>
                        {formatPercent(coin.price_change_percentage_24h)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>

        {/* Market News */}
        <motion.div
          className="lg:col-span-2"
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.25 }}
        >
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="section-title mb-0">Market News</h2>
              <Link to="/dashboard/news" className="text-xs text-brand-400 hover:text-brand-300">View all →</Link>
            </div>
            {loadingNews ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)}
              </div>
            ) : (
              <div className="space-y-3">
                {news?.slice(0, 4).map((item, i) => (
                  <NewsCard key={i} item={item} compact />
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Recent Sessions & Quick Actions */}
      <motion.div
        className="grid grid-cols-1 lg:grid-cols-2 gap-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title mb-0">Recent AI Chats</h2>
            <Link to="/dashboard/chat" className="text-xs text-brand-400 hover:text-brand-300">Open chat →</Link>
          </div>
          {sessions && sessions.length > 0 ? (
            <div className="space-y-2">
              {sessions.slice(0, 4).map((s) => (
                <Link key={s.session_id} to="/dashboard/chat" className="flex items-center gap-3 p-2 rounded-lg hover:bg-surface-700 transition-colors block">
                  <Activity className="w-4 h-4 text-brand-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-slate-200 truncate">{s.title || 'Chat session'}</div>
                    {s.last_message && <div className="text-xs text-slate-500 truncate">{s.last_message}</div>}
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-sm text-slate-500 text-center py-6">
              No chat sessions yet.{' '}
              <Link to="/dashboard/chat" className="text-brand-400 hover:underline">Start one</Link>
            </div>
          )}
        </div>

        <div className="card p-5">
          <h2 className="section-title mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Analyze Stock', to: '/dashboard/stocks', icon: TrendingUp },
              { label: 'Analyze Crypto', to: '/dashboard/crypto', icon: Activity },
              { label: 'Risk Analysis', to: '/dashboard/risk', icon: Shield },
              { label: 'AI Chat', to: '/dashboard/chat', icon: Activity },
            ].map(({ label, to, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                className="flex flex-col items-center gap-2 p-4 bg-surface-700 hover:bg-surface-600 rounded-xl transition-colors text-center"
              >
                <Icon className="w-5 h-5 text-brand-400" />
                <span className="text-xs font-medium text-slate-300">{label}</span>
              </Link>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  )
}
