import { z } from 'zod'

export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

export const registerSchema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string(),
}).refine((d) => d.password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
})

export const stockSearchSchema = z.object({
  symbol: z.string().min(1, 'Symbol required').max(10).toUpperCase(),
  period: z.enum(['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y']).default('1y'),
  include_technical: z.boolean().default(true),
  include_fundamental: z.boolean().default(true),
  include_news: z.boolean().default(true),
  include_sentiment: z.boolean().default(true),
})

export const cryptoSearchSchema = z.object({
  symbol: z.string().min(1, 'Symbol required'),
  vs_currency: z.string().default('usd'),
  days: z.number().min(1).max(365).default(30),
  include_sentiment: z.boolean().default(true),
})

export const riskAnalyzeSchema = z.object({
  symbols: z.array(z.string()).min(1, 'At least one symbol required'),
})

export const chatSchema = z.object({
  message: z.string().min(1, 'Message required').max(2000),
})

export const ragQuerySchema = z.object({
  query: z.string().min(3, 'Query must be at least 3 characters'),
})

export const portfolioCreateSchema = z.object({
  name: z.string().min(1, 'Portfolio name required'),
  description: z.string().optional(),
})

export type LoginFormValues = z.infer<typeof loginSchema>
export type RegisterFormValues = z.infer<typeof registerSchema>
export type StockSearchValues = z.infer<typeof stockSearchSchema>
export type CryptoSearchValues = z.infer<typeof cryptoSearchSchema>
export type RiskAnalyzeValues = z.infer<typeof riskAnalyzeSchema>
export type ChatFormValues = z.infer<typeof chatSchema>
export type RagQueryValues = z.infer<typeof ragQuerySchema>
export type PortfolioCreateValues = z.infer<typeof portfolioCreateSchema>
