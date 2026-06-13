import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi, stocksApi, cryptoApi, newsApi, riskApi, chatApi, ragApi, portfolioApi } from '../lib/api-client'
import { useAuthStore } from '../stores/auth-store'
import type {
  LoginRequest, RegisterRequest,
  StockAnalyzeRequest, CryptoAnalyzeRequest, RiskAnalyzeRequest,
  ChatRequest, RagQueryRequest, PortfolioCreate, Holding,
} from '../types'
import toast from 'react-hot-toast'

// ─── AUTH ─────────────────────────────────────────────────────
export const useCurrentUser = () => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: authApi.me,
    enabled: isAuthenticated,
  })
}

export const useLogin = () => {
  const { setTokens, setUser } = useAuthStore()
  return useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      const tokens = await authApi.login(credentials)
      setTokens(tokens.access_token, tokens.refresh_token)
      const user = await authApi.me()
      setUser(user)
      return { tokens, user }
    },
    onSuccess: (data) => {
      toast.success(`Welcome back, ${data.user.full_name || 'User'}!`)
    },
    onError: () => toast.error('Invalid credentials'),
  })
}

export const useRegister = () => {
  const { setTokens, setUser } = useAuthStore()
  return useMutation({
    mutationFn: async (data: RegisterRequest) => {
      await authApi.register(data)
      const tokens = await authApi.login({ email: data.email, password: data.password })
      setTokens(tokens.access_token, tokens.refresh_token)
      const user = await authApi.me()
      setUser(user)
      return { tokens, user }
    },
    onSuccess: () => {
      toast.success('Account created successfully!')
    },
    onError: () => toast.error('Registration failed'),
  })
}


export const useLogout = () => {
  const { logout } = useAuthStore()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      logout()
      qc.clear()
      toast.success('Logged out')
    },
  })
}

// ─── STOCKS ───────────────────────────────────────────────────
export const useStockPrice = (symbol: string, enabled = true) =>
  useQuery({ queryKey: ['stocks', 'price', symbol], queryFn: () => stocksApi.getPrice(symbol), enabled: !!symbol && enabled })

export const useStockTechnical = (symbol: string, enabled = true) =>
  useQuery({ queryKey: ['stocks', 'technical', symbol], queryFn: () => stocksApi.getTechnical(symbol), enabled: !!symbol && enabled })

export const useStockHistory = (symbol: string, enabled = true) =>
  useQuery({ queryKey: ['stocks', 'history', symbol], queryFn: () => stocksApi.getHistory(symbol), enabled: !!symbol && enabled })

export const useStockVolatility = (symbol: string, enabled = true) =>
  useQuery({ queryKey: ['stocks', 'volatility', symbol], queryFn: () => stocksApi.getVolatility(symbol), enabled: !!symbol && enabled })

export const useStockNews = (symbol: string, enabled = true) =>
  useQuery({ queryKey: ['stocks', 'news', symbol], queryFn: () => stocksApi.getNews(symbol), enabled: !!symbol && enabled })

export const useStockAnalyze = () =>
  useMutation({
    mutationFn: (data: StockAnalyzeRequest) => stocksApi.analyze(data),
    onError: () => toast.error('Stock analysis failed'),
  })

// ─── CRYPTO ───────────────────────────────────────────────────
export const useCryptoTop = () =>
  useQuery({ queryKey: ['crypto', 'top'], queryFn: cryptoApi.getTop, staleTime: 1000 * 60 })

export const useCryptoPrice = (symbol: string, enabled = true) =>
  useQuery({ queryKey: ['crypto', 'price', symbol], queryFn: () => cryptoApi.getPrice(symbol), enabled: !!symbol && enabled })

export const useCryptoAnalyze = () =>
  useMutation({
    mutationFn: (data: CryptoAnalyzeRequest) => cryptoApi.analyze(data),
    onError: () => toast.error('Crypto analysis failed'),
  })

// ─── NEWS ─────────────────────────────────────────────────────
export const useMarketNews = () =>
  useQuery({ queryKey: ['news', 'market'], queryFn: newsApi.getMarket, staleTime: 1000 * 60 * 5 })

export const useSymbolNews = (symbol: string, enabled = true) =>
  useQuery({ queryKey: ['news', 'symbol', symbol], queryFn: () => newsApi.getBySymbol(symbol), enabled: !!symbol && enabled })

// ─── RISK ─────────────────────────────────────────────────────
export const useRiskAnalyze = () =>
  useMutation({
    mutationFn: (data: RiskAnalyzeRequest) => riskApi.analyze(data),
    onError: () => toast.error('Risk analysis failed'),
  })

// ─── CHAT ─────────────────────────────────────────────────────
export const useChatSessions = () =>
  useQuery({ queryKey: ['chat', 'sessions'], queryFn: chatApi.getSessions })

export const useChatSession = (id: string, enabled = true) =>
  useQuery({ queryKey: ['chat', 'session', id], queryFn: () => chatApi.getSession(id), enabled: !!id && enabled })

export const useSendMessage = () =>
  useMutation({
    mutationFn: (data: ChatRequest) => chatApi.sendMessage(data),
    onError: () => toast.error('Failed to send message'),
  })

// ─── RAG ──────────────────────────────────────────────────────
export const useRagDocuments = () =>
  useQuery({ queryKey: ['rag', 'documents'], queryFn: ragApi.getDocuments })

export const useRagUpload = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => ragApi.upload(file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['rag', 'documents'] })
      toast.success('Document uploaded successfully')
    },
    onError: () => toast.error('Upload failed'),
  })
}

export const useRagQuery = () =>
  useMutation({
    mutationFn: (data: RagQueryRequest) => ragApi.query(data),
    onError: () => toast.error('Query failed'),
  })

// ─── PORTFOLIO ────────────────────────────────────────────────
export const usePortfolios = () =>
  useQuery({ queryKey: ['portfolio'], queryFn: portfolioApi.getAll })

export const usePortfolio = (id: string, enabled = true) =>
  useQuery({ queryKey: ['portfolio', id], queryFn: () => portfolioApi.get(id), enabled: !!id && enabled })

export const useCreatePortfolio = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: PortfolioCreate) => portfolioApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portfolio'] })
      toast.success('Portfolio created')
    },
    onError: () => toast.error('Failed to create portfolio'),
  })
}

export const useDeletePortfolio = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => portfolioApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portfolio'] })
      toast.success('Portfolio deleted')
    },
  })
}

export const useBuyAsset = (portfolioId: string) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { symbol: string; asset_type: string; quantity: number; price: number; notes?: string }) =>
      portfolioApi.buyAsset(portfolioId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portfolio'] })
      qc.invalidateQueries({ queryKey: ['portfolio', portfolioId] })
      qc.invalidateQueries({ queryKey: ['portfolio', portfolioId, 'performance'] })
      qc.invalidateQueries({ queryKey: ['portfolio', portfolioId, 'risk'] })
      toast.success('Buy transaction executed successfully')
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || 'Failed to execute buy transaction'
      toast.error(msg)
    },
  })
}

export const useSellAsset = (portfolioId: string) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { symbol: string; asset_type: string; quantity: number; price: number; notes?: string }) =>
      portfolioApi.sellAsset(portfolioId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portfolio'] })
      qc.invalidateQueries({ queryKey: ['portfolio', portfolioId] })
      qc.invalidateQueries({ queryKey: ['portfolio', portfolioId, 'performance'] })
      qc.invalidateQueries({ queryKey: ['portfolio', portfolioId, 'risk'] })
      toast.success('Sell transaction executed successfully')
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || 'Failed to execute sell transaction'
      toast.error(msg)
    },
  })
}

export const usePortfolioPerformance = (id: string, enabled = true) =>
  useQuery({ queryKey: ['portfolio', id, 'performance'], queryFn: () => portfolioApi.getPerformance(id), enabled: !!id && enabled })

export const usePortfolioRisk = (id: string, enabled = true) =>
  useQuery({ queryKey: ['portfolio', id, 'risk'], queryFn: () => portfolioApi.getRisk(id), enabled: !!id && enabled })
