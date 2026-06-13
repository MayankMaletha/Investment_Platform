import { Link, useLocation } from '@tanstack/react-router'
import {
  LayoutDashboard, TrendingUp, Bitcoin, Briefcase, Shield,
  Newspaper, MessageSquare, FileText, Settings, LogOut, ChevronLeft, ChevronRight,
  Zap
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { useLogout } from '../../hooks'
import { useState } from 'react'

const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { label: 'Stocks', icon: TrendingUp, path: '/dashboard/stocks' },
  { label: 'Crypto', icon: Bitcoin, path: '/dashboard/crypto' },
  { label: 'Portfolio', icon: Briefcase, path: '/dashboard/portfolio' },
  { label: 'Risk Analysis', icon: Shield, path: '/dashboard/risk' },
  { label: 'News', icon: Newspaper, path: '/dashboard/news' },
  { label: 'AI Chat', icon: MessageSquare, path: '/dashboard/chat' },
  { label: 'Documents', icon: FileText, path: '/dashboard/rag' },
  { label: 'Settings', icon: Settings, path: '/dashboard/settings' },
]

export function Sidebar() {
  const location = useLocation()
  const logout = useLogout()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={cn(
        'h-screen bg-surface-800 border-r border-surface-600 flex flex-col transition-all duration-300 sticky top-0 z-40',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-surface-600">
        <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center flex-shrink-0">
          <Zap className="w-4 h-4 text-white" />
        </div>
        {!collapsed && (
          <span className="font-bold text-slate-100 text-lg tracking-tight">InvestAI</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ label, icon: Icon, path }) => {
          const isActive = path === '/dashboard'
            ? location.pathname === '/dashboard'
            : location.pathname.startsWith(path)
          return (
            <Link
              key={path}
              to={path}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-brand-600/20 text-brand-400 border border-brand-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-surface-700'
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {!collapsed && label}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-2 pb-4 space-y-1 border-t border-surface-600 pt-3">
        <button
          onClick={() => logout.mutate()}
          className={cn(
            'flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-accent-red hover:bg-accent-red/10 transition-colors',
          )}
        >
          <LogOut className="w-4 h-4 flex-shrink-0" />
          {!collapsed && 'Sign out'}
        </button>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-slate-500 hover:text-slate-300 hover:bg-surface-700 transition-colors"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          {!collapsed && 'Collapse'}
        </button>
      </div>
    </aside>
  )
}
