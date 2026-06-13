import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: number, currency = 'USD', compact = false): string {
  if (compact && Math.abs(value) >= 1_000_000_000) {
    return `$${(value / 1_000_000_000).toFixed(2)}B`
  }
  if (compact && Math.abs(value) >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(2)}M`
  }
  if (compact && Math.abs(value) >= 1_000) {
    return `$${(value / 1_000).toFixed(1)}K`
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: value < 1 ? 6 : 2,
  }).format(value)
}

export function formatPercent(value: number, decimals = 2): string {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(decimals)}%`
}

export function formatNumber(value: number, compact = false): string {
  if (compact) {
    if (Math.abs(value) >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`
    if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
    if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(1)}K`
  }
  return new Intl.NumberFormat('en-US').format(value)
}

export function formatDate(dateStr: string, short = false): string {
  const date = new Date(dateStr)
  if (short) return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  })
}

export function getChangeColor(value: number): string {
  if (value > 0) return 'text-accent-green'
  if (value < 0) return 'text-accent-red'
  return 'text-slate-400'
}

export function getRecommendationColor(rec: string): string {
  if (['STRONG_BUY', 'BUY'].includes(rec)) return 'text-accent-green'
  if (['STRONG_SELL', 'SELL'].includes(rec)) return 'text-accent-red'
  return 'text-accent-yellow'
}

export function getRecommendationBadge(rec: string): string {
  if (['STRONG_BUY', 'BUY'].includes(rec)) return 'badge-green'
  if (['STRONG_SELL', 'SELL'].includes(rec)) return 'badge-red'
  return 'badge-yellow'
}

export function getRiskLevelColor(level: string): string {
  if (level === 'LOW') return 'text-accent-green'
  if (level === 'MODERATE') return 'text-accent-yellow'
  if (level === 'HIGH') return 'text-orange-400'
  return 'text-accent-red'
}

export function getSentimentColor(sentiment: string | undefined): string {
  if (sentiment === 'positive') return 'text-accent-green'
  if (sentiment === 'negative') return 'text-accent-red'
  return 'text-slate-400'
}

export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str
  return str.slice(0, maxLength) + '…'
}
