# InvestAI — AI Investment Agent Frontend

A complete, production-ready React 19 frontend for the FastAPI + LangGraph investment agent backend.

## Tech Stack

- **React 19** + **TypeScript** (strict, zero `any`)
- **Vite 5** — fast dev server and optimized builds
- **TanStack Router** — file-based routing with type-safe navigation
- **TanStack Query v5** — server state, caching, optimistic updates
- **Zustand** — client state (auth, chat)
- **Axios** — HTTP client with JWT interceptors and auto-refresh
- **Tailwind CSS** — dark-first design system
- **Framer Motion** — page transitions and UI animations
- **Recharts** — price charts, allocation pie, risk bars
- **React Hook Form + Zod** — typed validation for all forms
- **React Markdown** — chat message rendering
- **React Hot Toast** — toast notifications

---

## Quick Start

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Set your backend URL
echo "VITE_API_URL=http://127.0.0.1:8000" > .env

# 3. Install
npm install

# 4. Dev server
npm run dev

# 5. Production build
npm run build
```

---

## Project Structure

```
src/
├── lib/
│   ├── axios.ts          # Axios instance + JWT refresh interceptor
│   ├── api-client.ts     # All typed API calls (auth, stocks, crypto, news, risk, chat, rag, portfolio)
│   ├── query-client.ts   # TanStack Query client
│   ├── schemas.ts        # Zod validation schemas
│   └── utils.ts          # Formatters, color helpers
├── types/
│   └── index.ts          # Complete TypeScript interfaces for all API models
├── stores/
│   ├── auth-store.ts     # Zustand auth store (persisted to localStorage)
│   └── chat-store.ts     # Zustand chat session state
├── hooks/
│   └── index.ts          # All TanStack Query hooks for every endpoint
├── components/
│   ├── layout/
│   │   ├── DashboardLayout.tsx   # Sidebar + Navbar wrapper
│   │   ├── Sidebar.tsx           # Collapsible nav with active state
│   │   ├── Navbar.tsx            # Top bar with user menu
│   │   └── ProtectedRoute.tsx    # JWT-gated route wrapper
│   ├── ui/
│   │   ├── DashboardCard.tsx     # KPI metric card
│   │   ├── NewsCard.tsx          # News item with sentiment
│   │   ├── SearchBar.tsx         # Reusable search input
│   │   ├── LoadingSkeleton.tsx   # Skeleton loaders
│   │   └── EmptyState.tsx        # Empty + error states + ErrorBoundary
│   ├── agents/
│   │   └── AgentTracePanel.tsx   # Collapsible LangGraph agent output panel
│   └── charts/
│       ├── PriceChart.tsx        # Recharts area chart with SMA lines
│       └── AllocationChart.tsx   # Pie, performance line, risk bar, gauge
├── pages/
│   ├── LandingPage.tsx           # Marketing landing page
│   ├── auth/
│   │   ├── LoginPage.tsx
│   │   └── RegisterPage.tsx
│   └── dashboard/
│       ├── DashboardPage.tsx     # Overview with KPIs, crypto, news, quick actions
│       ├── StocksPage.tsx        # Full stock analysis with all technical indicators
│       ├── CryptoPage.tsx        # Crypto top list + detailed analysis
│       ├── PortfolioPage.tsx     # Portfolio CRUD + holdings + charts
│       ├── RiskPage.tsx          # Risk analysis with gauges and charts
│       ├── NewsPage.tsx          # News feed with sentiment filters
│       ├── ChatPage.tsx          # ChatGPT-style interface with agent trace
│       ├── RagPage.tsx           # Document upload + RAG query + citations
│       └── SettingsPage.tsx      # Profile, security, notifications, danger zone
└── App.tsx                       # TanStack Router config + route tree
```

---

## Backend Endpoints Integrated

### Auth
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh` — auto-called by axios interceptor
- `POST /api/v1/auth/logout`
- `GET  /api/v1/auth/me`

### Stocks
- `GET  /api/v1/stocks/price/{symbol}`
- `GET  /api/v1/stocks/technical/{symbol}`
- `GET  /api/v1/stocks/history/{symbol}`
- `GET  /api/v1/stocks/volatility/{symbol}`
- `GET  /api/v1/stocks/news/{symbol}`
- `POST /api/v1/stocks/analyze`

### Crypto
- `GET  /api/v1/crypto/top`
- `GET  /api/v1/crypto/price/{symbol}`
- `POST /api/v1/crypto/analyze`

### News
- `GET  /api/v1/news/market`
- `GET  /api/v1/news/symbol/{symbol}`

### Risk
- `POST /api/v1/risk/analyze`

### Chat
- `POST /api/v1/chat`
- `GET  /api/v1/chat/sessions`
- `GET  /api/v1/chat/sessions/{session_id}`

### RAG
- `POST /api/v1/rag/upload`
- `POST /api/v1/rag/query`
- `GET  /api/v1/rag/documents`

### Portfolio
- `GET    /api/v1/portfolio`
- `GET    /api/v1/portfolio/{id}`
- `POST   /api/v1/portfolio`
- `DELETE /api/v1/portfolio/{id}`
- `POST   /api/v1/portfolio/{id}/holdings`
- `DELETE /api/v1/portfolio/{id}/holdings/{symbol}`
- `GET    /api/v1/portfolio/{id}/performance`
- `GET    /api/v1/portfolio/{id}/risk`

---

## JWT Auth Flow

1. Login → tokens stored in Zustand (persisted to `localStorage`)
2. Every request → `Authorization: Bearer <access_token>` injected by axios interceptor
3. On 401 → interceptor calls `/auth/refresh`, queues failed requests, retries after new token
4. On refresh failure → clears store, redirects to `/login`

---

## LangGraph Agent Display

Every AI response that returns an `agents` array is displayed in the **AgentTracePanel** — a collapsible panel showing each agent's name, result, confidence bar, and reasoning text. Appears in:
- Stock analysis results
- Crypto analysis results
- Chat messages (per-message agent trace)

---

## Build

```bash
npm run build
# ✓ 3082 modules transformed
# dist/assets/index.js  ~1.26 MB (368 KB gzip)
# Zero TypeScript errors
```
