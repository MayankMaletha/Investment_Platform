import { useState } from 'react'
import { ChevronDown, ChevronUp, Brain, TrendingUp, Newspaper, Shield, Database, Star } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { AgentOutput } from '../../types'

const AGENT_ICONS: Record<string, React.ReactNode> = {
  technical: <TrendingUp className="w-4 h-4" />,
  news: <Newspaper className="w-4 h-4" />,
  sentiment: <Brain className="w-4 h-4" />,
  risk: <Shield className="w-4 h-4" />,
  memory: <Database className="w-4 h-4" />,
  recommendation: <Star className="w-4 h-4" />,
}

const AGENT_COLORS: Record<string, string> = {
  technical: 'text-brand-400',
  news: 'text-accent-purple',
  sentiment: 'text-accent-cyan',
  risk: 'text-accent-yellow',
  memory: 'text-slate-400',
  recommendation: 'text-accent-green',
}

function getAgentKey(name: string): string {
  return name.toLowerCase().replace(/\s+agent$/i, '').trim()
}

interface AgentCardProps {
  agent: AgentOutput
}

export function AgentCard({ agent }: AgentCardProps) {
  const key = getAgentKey(agent.agent)
  const icon = AGENT_ICONS[key] || <Brain className="w-4 h-4" />
  const color = AGENT_COLORS[key] || 'text-slate-400'
  const confidence = Math.round(agent.confidence * (agent.confidence <= 1 ? 100 : 1))

  const resultColor =
    ['bullish', 'positive', 'buy', 'strong_buy'].some(k => agent.result?.toLowerCase().includes(k))
      ? 'text-accent-green'
      : ['bearish', 'negative', 'sell', 'strong_sell'].some(k => agent.result?.toLowerCase().includes(k))
        ? 'text-accent-red'
        : 'text-accent-yellow'

  return (
    <div className="bg-surface-700 rounded-lg p-3 border border-surface-500">
      <div className="flex items-center justify-between mb-2">
        <div className={cn('flex items-center gap-2 text-sm font-medium', color)}>
          {icon}
          <span>{agent.agent}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-16 h-1.5 bg-surface-600 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-500 rounded-full"
              style={{ width: `${confidence}%` }}
            />
          </div>
          <span className="text-xs text-slate-400">{confidence}%</span>
        </div>
      </div>
      <div className={cn('text-sm font-semibold mb-1', resultColor)}>{agent.result}</div>
      {agent.reasoning && (
        <p className="text-xs text-slate-500 leading-relaxed">{agent.reasoning}</p>
      )}
    </div>
  )
}

interface AgentTracePanelProps {
  agents: AgentOutput[]
  className?: string
}

export function AgentTracePanel({ agents, className }: AgentTracePanelProps) {
  const [isOpen, setIsOpen] = useState(false)

  if (!agents || agents.length === 0) return null

  return (
    <div className={cn('card border border-surface-500', className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 hover:bg-surface-700/50 transition-colors rounded-xl"
      >
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-brand-400" />
          <span className="text-sm font-medium text-slate-300">Agent Trace</span>
          <span className="text-xs text-slate-500 bg-surface-700 px-2 py-0.5 rounded-full">
            {agents.length} agents
          </span>
        </div>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        )}
      </button>
      {isOpen && (
        <div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {agents.map((agent, i) => (
            <AgentCard key={i} agent={agent} />
          ))}
        </div>
      )}
    </div>
  )
}
