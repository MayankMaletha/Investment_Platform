import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Plus, MessageSquare, Bot, User, ChevronRight } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { useChatSessions, useSendMessage, useChatSession } from '../../hooks'
import { useChatStore } from '../../stores/chat-store'
import { AgentTracePanel } from '../../components/agents/AgentTracePanel'
import { formatDateTime } from '../../lib/utils'
import type { ChatMessage } from '../../types'

const SUGGESTED_PROMPTS = [
  'Analyze Apple stock briefly',
  'What are the top crypto trends right now?',
  'How should I diversify my portfolio?',
  'Explain the current market sentiment',
  'What is the risk of investing in tech stocks?',
]

export function ChatPage() {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const { data: sessions } = useChatSessions()
  const sendMessage = useSendMessage()
  const {
    messages, currentSessionId, isLoading,
    addMessage, setMessages, setCurrentSession, setLoading, clearMessages
  } = useChatStore()

  const { data: sessionData } = useChatSession(currentSessionId || '', !!currentSessionId && messages.length === 0)

  useEffect(() => {
    if (sessionData?.messages) setMessages(sessionData.messages)
  }, [sessionData])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = async (text?: string) => {
    const msg = text || input.trim()
    if (!msg || isLoading) return
    setInput('')

    const userMsg: ChatMessage = { role: 'user', content: msg, timestamp: new Date().toISOString() }
    addMessage(userMsg)
    setLoading(true)

    try {
      const response = await sendMessage.mutateAsync({
        message: msg,
        session_id: currentSessionId || undefined,
        context: { risk_tolerance: 'moderate' },
      })
      setCurrentSession(response.session_id)
      const aiMsg: ChatMessage = {
        role: 'assistant',
        content: response.message,
        timestamp: response.timestamp,
        agents: response.agents,
      }
      addMessage(aiMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] max-w-6xl gap-4">
      {/* Sessions Sidebar */}
      <div className="w-64 flex-shrink-0 flex flex-col gap-2">
        <button
          onClick={clearMessages}
          className="btn-primary w-full flex items-center gap-2 justify-center"
        >
          <Plus className="w-4 h-4" /> New Chat
        </button>
        <div className="card flex-1 overflow-y-auto p-2 space-y-1">
          <div className="text-xs text-slate-500 px-2 py-1">Recent sessions</div>
          {sessions && sessions.length > 0 ? (
            sessions.map((s) => (
              <button
                key={s.session_id}
                onClick={() => {
                  setCurrentSession(s.session_id)
                  setMessages([])
                }}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  currentSessionId === s.session_id
                    ? 'bg-brand-600/20 text-brand-400'
                    : 'text-slate-400 hover:bg-surface-700 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
                  <span className="truncate">{s.title || 'Chat session'}</span>
                </div>
                <div className="text-xs text-slate-600 mt-0.5 pl-5">{formatDateTime(s.updated_at)}</div>
              </button>
            ))
          ) : (
            <div className="text-xs text-slate-600 text-center py-4">No sessions yet</div>
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col card overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && !isLoading && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-14 h-14 bg-brand-600/20 rounded-full flex items-center justify-center mb-4">
                <Bot className="w-7 h-7 text-brand-400" />
              </div>
              <h3 className="text-slate-200 font-medium mb-1">InvestAI Assistant</h3>
              <p className="text-slate-500 text-sm mb-6">Ask me anything about stocks, crypto, markets, or your portfolio</p>
              <div className="space-y-2 w-full max-w-md">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSend(prompt)}
                    className="w-full text-left text-sm px-4 py-2.5 bg-surface-700 hover:bg-surface-600 text-slate-300 rounded-lg transition-colors flex items-center justify-between group"
                  >
                    {prompt}
                    <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-400" />
                  </button>
                ))}
              </div>
            </div>
          )}

          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 bg-brand-600/20 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <Bot className="w-3.5 h-3.5 text-brand-400" />
                  </div>
                )}
                <div className={`max-w-[80%] space-y-2 ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col`}>
                  <div
                    className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-brand-600 text-white rounded-tr-sm'
                        : 'bg-surface-700 text-slate-200 rounded-tl-sm'
                    }`}
                  >
                    {msg.role === 'assistant' ? (
                      <div className="prose prose-sm prose-invert max-w-none">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      msg.content
                    )}
                  </div>
                  <span className="text-xs text-slate-600 px-1">{formatDateTime(msg.timestamp)}</span>
                  {msg.agents && msg.agents.length > 0 && (
                    <AgentTracePanel agents={msg.agents} className="w-full" />
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="w-7 h-7 bg-surface-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <User className="w-3.5 h-3.5 text-slate-400" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {isLoading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3 justify-start">
              <div className="w-7 h-7 bg-brand-600/20 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <Bot className="w-3.5 h-3.5 text-brand-400" />
              </div>
              <div className="bg-surface-700 rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="flex gap-1 items-center h-4">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-surface-600 p-4">
          <div className="flex gap-3 items-end">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about markets, stocks, crypto, or your portfolio..."
              rows={1}
              className="input flex-1 resize-none max-h-32 overflow-y-auto"
              style={{ minHeight: '40px' }}
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
              className="btn-primary h-10 w-10 flex items-center justify-center flex-shrink-0 p-0"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-slate-600 mt-2">Press Enter to send, Shift+Enter for new line</p>
        </div>
      </div>
    </div>
  )
}
