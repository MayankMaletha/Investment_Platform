import { Search, X } from 'lucide-react'
import { useState } from 'react'
import { cn } from '../../lib/utils'

interface SearchBarProps {
  placeholder?: string
  onSearch: (value: string) => void
  className?: string
  defaultValue?: string
}

export function SearchBar({ placeholder = 'Search...', onSearch, className, defaultValue = '' }: SearchBarProps) {
  const [value, setValue] = useState(defaultValue)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (value.trim()) onSearch(value.trim().toUpperCase())
  }

  return (
    <form onSubmit={handleSubmit} className={cn('relative', className)}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        className="input w-full pl-9 pr-10 h-10"
      />
      {value && (
        <button
          type="button"
          onClick={() => setValue('')}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </form>
  )
}
