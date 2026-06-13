// ─── AUTH ─────────────────────────────────────────────────────
export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  created_at: string
}

// ─── AGENT OUTPUTS ────────────────────────────────────────────
export interface AgentOutput {
  agent: string
  result: string
  confidence: number
  reasoning: string
  signal?: string
  sentiment?: string
}

// ─── STOCKS ───────────────────────────────────────────────────
export interface StockPrice {
  symbol: string
  price: number
  change: number
  change_percent: number
  volume: number
  market_cap?: number
  timestamp: string
}

export interface StockTechnical {
  symbol: string
  rsi: number
  macd: number
  macd_signal: number
  macd_histogram: number
  sma20: number
  sma50: number
  sma200: number
  bb_upper: number
  bb_lower: number
  bb_middle: number
  signals: TechnicalSignal[]
}

export interface TechnicalSignal {
  indicator: string
  signal: 'BUY' | 'SELL' | 'HOLD' | 'NEUTRAL'
  value: number
  description: string
}

export interface HistoryPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  sma20?: number
  sma50?: number
  sma200?: number
}

export interface StockHistory {
  symbol: string
  period: string
  data: HistoryPoint[]
}

export interface StockVolatility {
  symbol: string
  volatility_30d: number
  volatility_90d: number
  beta: number
  var_95: number
  max_drawdown: number
}

export interface StockAnalyzeRequest {
  symbol: string
  period?: string
  include_technical?: boolean
  include_fundamental?: boolean
  include_news?: boolean
  include_sentiment?: boolean
}

export interface StockAnalysis {
  symbol: string
  price: StockPrice
  technical?: StockTechnical
  volatility?: StockVolatility
  news?: NewsItem[]
  agents: AgentOutput[]
  recommendation: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL'
  confidence: number
  summary: string
  timestamp: string
}

// ─── CRYPTO ───────────────────────────────────────────────────
export interface CryptoTop {
  id: string
  symbol: string
  name: string
  image: string
  current_price: number
  price_change_24h: number
  price_change_percentage_24h: number
  market_cap: number
  volume_24h: number
  rank: number
}

export interface CryptoPrice {
  id: string
  symbol: string
  name: string
  current_price: number
  price_change_24h: number
  price_change_percentage_24h: number
  market_cap: number
  total_volume: number
  high_24h: number
  low_24h: number
  sparkline?: number[]
  timestamp: string
}

export interface CryptoAnalyzeRequest {
  symbol: string
  vs_currency?: string
  days?: number
  include_sentiment?: boolean
}

export interface CryptoAnalysis {
  symbol: string
  name: string
  price: CryptoPrice
  trend: string
  agents: AgentOutput[]
  recommendation: string
  confidence: number
  sentiment_score: number
  summary: string
  price_history?: { date: string; price: number }[]
  timestamp: string
}

// ─── NEWS ─────────────────────────────────────────────────────
export interface NewsItem {
  id?: string
  title: string
  summary?: string
  description?: string
  url: string
  source: string
  published_at: string
  sentiment?: 'positive' | 'negative' | 'neutral'
  sentiment_score?: number
  category?: string
  symbols?: string[]
  image_url?: string
}

// ─── RISK ─────────────────────────────────────────────────────
export interface RiskAnalyzeRequest {
  symbols?: string[]
  portfolio_id?: string
}

export interface SymbolRisk {
  symbol: string
  weight: number
  volatility: number
  beta: number
  var_95: number
  contribution: number
}

export interface RiskAnalysis {
  risk_score: number
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH'
  portfolio_beta: number
  portfolio_volatility: number
  sharpe_ratio: number
  max_drawdown: number
  var_95: number
  diversification_score: number
  symbols: SymbolRisk[]
  recommendations: string[]
  timestamp: string
}

// ─── CHAT ─────────────────────────────────────────────────────
export interface ChatRequest {
  message: string
  session_id?: string
  context?: Record<string, string>
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  agents?: AgentOutput[]
}

export interface ChatSession {
  session_id: string
  title?: string
  created_at: string
  updated_at: string
  message_count?: number
  last_message?: string
}

export interface ChatResponse {
  session_id: string
  message: string
  agents?: AgentOutput[]
  timestamp: string
}

// ─── RAG ──────────────────────────────────────────────────────
export interface RagDocument {
  id: string
  filename: string
  file_type: string
  size: number
  status: 'processing' | 'ready' | 'error'
  chunk_count?: number
  uploaded_at: string
  metadata?: Record<string, string>
}

export interface RagQueryRequest {
  query: string
  document_ids?: string[]
  top_k?: number
}

export interface RagCitation {
  document_id: string
  filename: string
  page?: number
  chunk_text: string
  score: number
}

export interface RagQueryResponse {
  query: string
  answer: string
  citations: RagCitation[]
  confidence: number
  timestamp: string
}

// ─── PORTFOLIO ────────────────────────────────────────────────
export interface Holding {
  symbol: string
  name?: string
  quantity: number
  average_cost: number
  current_price?: number
  current_value?: number
  gain_loss?: number
  gain_loss_percent?: number
  sector?: string
  asset_type?: 'stock' | 'crypto' | 'etf'
}

export interface PortfolioCreate {
  name: string
  description?: string
}

export interface Portfolio {
  id: string
  name: string
  description?: string
  user_id: string
  holdings: Holding[]
  total_value: number
  total_cost?: number
  total_gain_loss?: number
  total_gain_loss_percent?: number
  beta?: number
  volatility?: number
  sharpe_ratio?: number
  diversification_score?: number
  risk_score?: number
  sector_allocation?: Record<string, number>
  performance?: PerformancePoint[]
  created_at: string
  updated_at: string
}

export interface PerformancePoint {
  date: string
  value: number
  return_percent?: number
}
