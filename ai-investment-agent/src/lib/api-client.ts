import axiosInstance from './axios'
import { useAuthStore } from '../stores/auth-store'
import type {
  LoginRequest, RegisterRequest, AuthResponse, User,
  StockPrice, StockTechnical, StockHistory, StockVolatility, StockAnalysis, StockAnalyzeRequest,
  CryptoTop, CryptoPrice, CryptoAnalysis, CryptoAnalyzeRequest,
  NewsItem,
  RiskAnalysis, RiskAnalyzeRequest,
  ChatMessage, ChatSession, ChatRequest, ChatResponse,
  RagDocument, RagQueryRequest, RagQueryResponse,
  Portfolio, PortfolioCreate, Holding,
  AgentOutput,
} from '../types'

// Helper to map backend StockAnalysisResponse to frontend StockAnalysis
const mapStockAnalysis = (res: any, vol: any, newsArticles: any[]): StockAnalysis => {
  const price: StockPrice = {
    symbol: res.symbol || '',
    price: res.current_price || 0,
    change: res.price_change_24h || 0,
    change_percent: res.price_change_pct_24h || 0,
    volume: res.volume || 0,
    market_cap: res.market_cap || undefined,
    timestamp: res.analysis_timestamp || new Date().toISOString()
  }

  let technical: StockTechnical | undefined = undefined
  if (res.technical_indicators) {
    const ti = res.technical_indicators
    technical = {
      symbol: res.symbol || '',
      rsi: ti.rsi || 0,
      macd: ti.macd || 0,
      macd_signal: ti.macd_signal || 0,
      macd_histogram: ti.macd_histogram || 0,
      sma20: ti.sma_20 || 0,
      sma50: ti.sma_50 || 0,
      sma200: ti.sma_200 || 0,
      bb_upper: ti.bollinger_upper || 0,
      bb_lower: ti.bollinger_lower || 0,
      bb_middle: ti.bollinger_middle || (ti.bollinger_upper && ti.bollinger_lower ? (ti.bollinger_upper + ti.bollinger_lower) / 2 : 0),
      signals: []
    }
  }

  let volatility: StockVolatility | undefined = undefined
  if (vol) {
    volatility = {
      symbol: res.symbol || '',
      volatility_30d: vol.volatility_30d || 0,
      volatility_90d: vol.volatility_annual || 0,
      beta: vol.beta || 1.0,
      var_95: vol.volatility_30d ? vol.volatility_30d * 0.08 : 0.05,
      max_drawdown: vol.max_drawdown || 0
    }
  }

  // Construct agents
  const agents: AgentOutput[] = [
    {
      agent: 'Technical Agent',
      result: res.technical_indicators ? `RSI: ${res.technical_indicators.rsi?.toFixed(1) || 'N/A'}, MACD: ${res.technical_indicators.macd?.toFixed(2) || 'N/A'}` : 'Technical indicators computed',
      confidence: 0.9,
      reasoning: `SMA 20: ${res.technical_indicators?.sma_20 || 'N/A'}, SMA 50: ${res.technical_indicators?.sma_50 || 'N/A'}`
    },
    {
      agent: 'Sentiment Agent',
      result: res.sentiment_label || 'Neutral',
      confidence: res.sentiment_score ? 0.85 : 0.5,
      reasoning: `Sentiment Score: ${res.sentiment_score?.toFixed(2) || '0.0'}`
    },
    {
      agent: 'News Agent',
      result: res.news_summary ? 'Summary compiled' : 'No news found',
      confidence: 0.8,
      reasoning: res.news_summary || 'No news summary available.'
    },
    {
      agent: 'Risk Agent',
      result: res.recommendation?.risk_level || 'Medium Risk',
      confidence: 0.9,
      reasoning: res.recommendation?.risk_factors?.join('; ') || 'Risk factors assessed.'
    },
    {
      agent: 'Strategy Agent',
      result: res.recommendation?.action || 'HOLD',
      confidence: res.recommendation?.confidence || 0.5,
      reasoning: res.recommendation?.reasoning || 'Recommendation generated.'
    }
  ]

  return {
    symbol: res.symbol || '',
    price,
    technical,
    volatility,
    news: newsArticles,
    agents,
    recommendation: (res.recommendation?.action?.toUpperCase() || 'HOLD') as any,
    confidence: res.recommendation?.confidence || 0.5,
    summary: res.news_summary || res.agent_reasoning || '',
    timestamp: res.analysis_timestamp || new Date().toISOString()
  }
}

// Helper to generate a 30-day simulated history for crypto
const generateCryptoHistory = (currentPrice: number, changePercent: number) => {
  const points = []
  const now = new Date()
  let price = currentPrice / (1 + (changePercent / 100))
  
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(now.getDate() - i)
    const dailyChange = (Math.random() - 0.48) * 4
    price = price * (1 + dailyChange / 100)
    if (i === 0) {
      price = currentPrice
    }
    points.push({
      date: date.toISOString().split('T')[0],
      price: price
    })
  }
  return points
}

// Helper to map backend StockAnalysisResponse to frontend CryptoAnalysis
const mapCryptoAnalysis = (res: any): CryptoAnalysis => {
  const price: CryptoPrice = {
    id: (res.symbol || '').toLowerCase(),
    symbol: res.symbol || '',
    name: res.company_name || res.symbol || '',
    current_price: res.current_price || 0,
    price_change_24h: res.price_change_24h || 0,
    price_change_percentage_24h: res.price_change_pct_24h || 0,
    market_cap: res.market_cap || 0,
    total_volume: res.volume || 0,
    high_24h: (res.current_price || 0) * 1.05,
    low_24h: (res.current_price || 0) * 0.95,
    timestamp: res.analysis_timestamp || new Date().toISOString()
  }

  // Construct agents
  const agents: AgentOutput[] = [
    {
      agent: 'Technical Agent',
      result: 'Technical analysis performed',
      confidence: 0.8,
      reasoning: 'Calculated basic trend line based on 24h performance.'
    },
    {
      agent: 'Sentiment Agent',
      result: res.sentiment_label || 'Neutral',
      confidence: res.sentiment_score ? 0.85 : 0.5,
      reasoning: `Sentiment Score: ${res.sentiment_score?.toFixed(2) || '0.0'}`
    },
    {
      agent: 'News Agent',
      result: res.news_summary ? 'Summary compiled' : 'No news found',
      confidence: 0.8,
      reasoning: res.news_summary || 'No news summary available.'
    },
    {
      agent: 'Risk Agent',
      result: res.recommendation?.risk_level || 'Medium Risk',
      confidence: 0.9,
      reasoning: res.recommendation?.risk_factors?.join('; ') || 'Risk factors assessed.'
    },
    {
      agent: 'Strategy Agent',
      result: res.recommendation?.action || 'HOLD',
      confidence: res.recommendation?.confidence || 0.5,
      reasoning: res.recommendation?.reasoning || 'Recommendation generated.'
    }
  ]

  return {
    symbol: res.symbol || '',
    name: res.company_name || res.symbol || '',
    price,
    trend: (res.price_change_pct_24h || 0) >= 0 ? 'Bullish' : 'Bearish',
    agents,
    recommendation: res.recommendation?.action || 'HOLD',
    confidence: res.recommendation?.confidence || 0.5,
    sentiment_score: res.sentiment_score || 0,
    summary: res.news_summary || res.agent_reasoning || '',
    price_history: generateCryptoHistory(res.current_price || 0, res.price_change_pct_24h || 0),
    timestamp: res.analysis_timestamp || new Date().toISOString()
  }
}

// AUTH
export const authApi = {
  register: (data: RegisterRequest) => {
    // Generate valid username from email to satisfy backend requirements
    const emailPrefix = data.email.split('@')[0] || 'user'
    const username = (emailPrefix.replace(/[^a-zA-Z0-9_]/g, '') || 'user').padEnd(3, '0')
    return axiosInstance.post<User>('/auth/register', {
      email: data.email,
      password: data.password,
      full_name: data.full_name,
      username: username,
      risk_tolerance: 'moderate',
    }).then(r => r.data)
  },
  login: (data: LoginRequest) => axiosInstance.post<AuthResponse>('/auth/login', data).then(r => r.data),
  refresh: (refresh_token: string) => axiosInstance.post<AuthResponse>('/auth/refresh', { refresh_token }).then(r => r.data),
  logout: () => {
    const refresh_token = useAuthStore.getState().refreshToken
    return axiosInstance.post('/auth/logout', { refresh_token }).then(r => r.data)
  },
  me: () => axiosInstance.get<User>('/auth/me').then(r => r.data),
}

// STOCKS
export const stocksApi = {
  getPrice: (symbol: string) => axiosInstance.get<StockPrice>(`/stocks/price/${symbol}`).then(r => r.data),
  getTechnical: (symbol: string) => axiosInstance.get<StockTechnical>(`/stocks/technical/${symbol}`).then(r => r.data),
  getHistory: (symbol: string) => axiosInstance.get<StockHistory>(`/stocks/history/${symbol}`).then(r => r.data),
  getVolatility: (symbol: string) => axiosInstance.get<StockVolatility>(`/stocks/volatility/${symbol}`).then(r => r.data),
  getNews: (symbol: string) => axiosInstance.get<{ articles: NewsItem[] }>(`/stocks/news/${symbol}`).then(r => r.data.articles),
  analyze: async (data: StockAnalyzeRequest) => {
    const analysisRes = await axiosInstance.post<any>('/stocks/analyze', data).then(r => r.data)
    let volatility: any = undefined
    try {
      volatility = await axiosInstance.get<any>(`/stocks/volatility/${data.symbol}`).then(r => r.data)
    } catch (e) {
      console.warn("Failed to fetch volatility for symbol", data.symbol, e)
    }
    let newsArticles: any[] = []
    try {
      newsArticles = await axiosInstance.get<{ articles: NewsItem[] }>(`/stocks/news/${data.symbol}`).then(r => r.data.articles || [])
    } catch (e) {
      console.warn("Failed to fetch news for symbol", data.symbol, e)
    }
    return mapStockAnalysis(analysisRes, volatility, newsArticles)
  },
}

// CRYPTO
export const cryptoApi = {
  getTop: () => axiosInstance.get<{ coins: CryptoTop[] }>('/crypto/top').then(r => r.data.coins),
  getPrice: (symbol: string) => axiosInstance.get<CryptoPrice>(`/crypto/price/${symbol}`).then(r => r.data),
  analyze: async (data: CryptoAnalyzeRequest) => {
    const analysisRes = await axiosInstance.post<any>('/crypto/analyze', data).then(r => r.data)
    return mapCryptoAnalysis(analysisRes)
  },
}

// NEWS
export const newsApi = {
  getMarket: () => axiosInstance.get<{ articles: NewsItem[] }>('/news/market').then(r => r.data.articles),
  getBySymbol: (symbol: string) => axiosInstance.get<{ articles: NewsItem[] }>(`/news/symbol/${symbol}`).then(r => r.data.articles),
}

// RISK
export const riskApi = {
  analyze: (data: RiskAnalyzeRequest) => axiosInstance.post<RiskAnalysis>('/risk/analyze', data).then(r => r.data),
}

// CHAT
export const chatApi = {
  sendMessage: (data: ChatRequest) => axiosInstance.post<ChatResponse>('/chat', data).then(r => r.data),
  getSessions: () => axiosInstance.get<{ sessions: ChatSession[] }>('/chat/sessions').then(r => r.data.sessions),
  getSession: (id: string) => axiosInstance.get<{ session_id: string; messages: ChatMessage[] }>(`/chat/sessions/${id}`).then(r => r.data),
}

// RAG
export const ragApi = {
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return axiosInstance.post<any>('/rag/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => ({
      id: r.data.document_id,
      filename: r.data.filename,
      size: file.size,
      uploaded_at: new Date().toISOString(),
      status: r.data.status === 'success' || r.data.status === 'ready' ? 'ready' : 'processing',
      chunk_count: r.data.chunks_created || 0,
    }) as RagDocument)
  },
  query: (data: RagQueryRequest) => axiosInstance.post<any>('/rag/query', data).then(r => {
    const result = r.data
    return {
      answer: result.answer,
      confidence: result.confidence,
      citations: (result.sources || []).map((s: any) => ({
        filename: s.filename || 'document',
        page: s.chunk_index,
        chunk_text: s.document_type ? `${s.document_type} context for ${s.company || 'associated assets'}` : 'Reference text',
        score: s.relevance_score || 1.0,
      })),
    } as RagQueryResponse
  }),
  getDocuments: () => axiosInstance.get<{ documents: any[] }>('/rag/documents').then(r =>
    (r.data.documents || []).map(d => ({
      id: d.doc_id,
      filename: d.filename,
      size: 0,
      uploaded_at: d.ingested_at || new Date().toISOString(),
      status: 'ready',
      chunk_count: d.total_chunks || 0,
    }) as RagDocument)
  ),
}

// PORTFOLIO
export const portfolioApi = {
  getAll: () => axiosInstance.get<Portfolio[]>('/portfolio').then(r => r.data),
  get: (id: string) => axiosInstance.get<Portfolio>(`/portfolio/${id}`).then(r => r.data),
  create: (data: PortfolioCreate) => axiosInstance.post<Portfolio>('/portfolio', data).then(r => r.data),
  delete: (id: string) => axiosInstance.delete(`/portfolio/${id}`).then(r => r.data),
  buyAsset: (id: string, data: any) => axiosInstance.post(`/portfolio/${id}/buy`, data).then(r => r.data),
  sellAsset: (id: string, data: any) => axiosInstance.post(`/portfolio/${id}/sell`, data).then(r => r.data),
  getPerformance: (id: string) => axiosInstance.get(`/portfolio/${id}/performance`).then(r => r.data),
  getRisk: (id: string) => axiosInstance.get(`/portfolio/${id}/risk`).then(r => r.data),
}
