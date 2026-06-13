import { cn } from '../../lib/utils'

interface DashboardCardProps {
  title: string
  value: string
  subtitle?: string
  icon?: React.ReactNode
  trend?: number
  className?: string
  children?: React.ReactNode
  badge?: React.ReactNode
}

export function DashboardCard({
  title, value, subtitle, icon, trend, className, children, badge
}: DashboardCardProps) {
  return (
    <div className={cn('card p-5', className)}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          {icon && (
            <div className="w-9 h-9 bg-surface-700 rounded-lg flex items-center justify-center text-brand-400">
              {icon}
            </div>
          )}
          <span className="text-slate-400 text-sm font-medium">{title}</span>
        </div>
        {badge}
      </div>
      <div className="text-2xl font-bold text-slate-100 mb-1">{value}</div>
      {subtitle && (
        <div className="flex items-center gap-2">
          {trend !== undefined && (
            <span className={trend >= 0 ? 'text-accent-green text-sm' : 'text-accent-red text-sm'}>
              {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(2)}%
            </span>
          )}
          <span className="text-slate-500 text-xs">{subtitle}</span>
        </div>
      )}
      {children}
    </div>
  )
}
