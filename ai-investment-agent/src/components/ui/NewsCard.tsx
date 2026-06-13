import { ExternalLink, Clock } from 'lucide-react'
import { formatDateTime, getSentimentColor, truncate } from '../../lib/utils'
import type { NewsItem } from '../../types'

interface NewsCardProps {
  item: NewsItem
  compact?: boolean
}

export function NewsCard({ item, compact = false }: NewsCardProps) {
  const sentimentColor = getSentimentColor(item.sentiment)

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className="card-hover p-4 flex flex-col gap-2 block"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className={`text-slate-200 text-sm font-medium leading-snug ${compact ? 'line-clamp-2' : ''}`}>
          {item.title}
        </h3>
        <ExternalLink className="w-3.5 h-3.5 text-slate-500 flex-shrink-0 mt-0.5" />
      </div>
      {!compact && (item.summary || item.description) && (
        <p className="text-slate-500 text-xs leading-relaxed">
          {truncate(item.summary || item.description || '', 150)}
        </p>
      )}
      <div className="flex items-center justify-between mt-1">
        <div className="flex items-center gap-2">
          <span className="text-slate-500 text-xs font-medium">{item.source}</span>
          {item.sentiment && (
            <span className={`text-xs font-medium ${sentimentColor}`}>
              {item.sentiment}
            </span>
          )}
          {item.category && (
            <span className="badge-blue">{item.category}</span>
          )}
        </div>
        <div className="flex items-center gap-1 text-slate-600 text-xs">
          <Clock className="w-3 h-3" />
          {formatDateTime(item.published_at)}
        </div>
      </div>
    </a>
  )
}
