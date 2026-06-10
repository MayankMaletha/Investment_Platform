# AI Investment Agent — Backend

A production-grade, multi-agent AI investment analysis platform built with FastAPI, LangChain, LangGraph, and modern async Python.

## Architecture Overview

```
User Request
    │
    ▼
FastAPI (HTTP / WebSocket)
    │
    ▼
LangGraph Multi-Agent Workflow
    ├── MemoryAgent     → ChromaDB long-term memory retrieval
    ├── FinancialAgent  → Finnhub market data + pandas/numpy technicals
    ├── NewsAgent       → NewsAPI + FinBERT sentiment
    ├── SentimentAgent  → Composite sentiment scoring
    ├── RiskAgent       → Volatility, beta, drawdown, VaR
    └── StrategyAgent   → GPT-4o / rule-based recommendation
    │
    ▼
PostgreSQL (users, portfolios, transactions, chat history)
ChromaDB   (vector memory, RAG document store)
Redis      (analysis result caching)
```

## Quick Start

### With Docker (recommended)

```bash
# 1. Copy and fill environment variables
cp .env
# Edit .env — add FINNHUB_API_KEY and NEWS_API_KEY

# 2. Start all services
docker compose up

# 3. API available at http://localhost:8080
# 4. Swagger docs at http://localhost:8080/docs (DEBUG=true only)
```

### Local Development

```bash
# Prerequisites: Python 3.11+, PostgreSQL, Redis, ChromaDB

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env  # edit with your API keys

# Run database migrations (first time)
alembic upgrade head

# Start the server
uvicorn main:app --reload --port 8080
```

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Login, get JWT tokens |
| POST | `/api/v1/auth/refresh` | Rotate refresh token |
| POST | `/api/v1/auth/logout` | Revoke refresh token |
| GET  | `/api/v1/auth/me` | Current user profile |

### Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/stocks/analyze` | Full multi-agent stock analysis |
| POST | `/api/v1/crypto/analyze` | Full crypto analysis |
| GET  | `/api/v1/stocks/price/{symbol}` | Quick price lookup |
| GET  | `/api/v1/stocks/technical/{symbol}` | Technical indicators |

### Portfolio
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/v1/portfolio/` | List portfolios |
| POST | `/api/v1/portfolio/` | Create portfolio |
| POST | `/api/v1/portfolio/{id}/buy` | Execute buy |
| POST | `/api/v1/portfolio/{id}/sell` | Execute sell |
| GET  | `/api/v1/portfolio/{id}/transactions` | Transaction history |

### AI Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/` | Chat with AI advisor |
| GET  | `/api/v1/chat/sessions` | List sessions |
| GET  | `/api/v1/chat/sessions/{id}` | Get session history |

### RAG Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/rag/upload` | Upload PDF (SEC filing, annual report) |
| POST | `/api/v1/rag/query` | Query across documents |
| GET  | `/api/v1/rag/documents` | List ingested documents |

### WebSocket
Connect to `ws://localhost:8080/ws?token=<JWT_ACCESS_TOKEN>`

**Actions:**
```json
{"action": "subscribe",   "symbol": "AAPL"}
{"action": "unsubscribe", "symbol": "AAPL"}
{"action": "analyze",     "symbol": "AAPL"}
{"action": "ping"}
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run only agent tests
pytest tests/test_agents.py -v
```

## Project Structure

```
backend/
├── agents/                 # Individual AI agents (financial, news, sentiment, risk, strategy, memory)
├── api/routes/             # FastAPI route handlers (thin — call services)
├── auth/                   # JWT handling, password hashing
├── core/                   # Logging, exceptions, dependency injection
├── database/               # SQLAlchemy models, repositories, session
├── langgraph_workflow/     # Multi-agent graph definition
├── memory/                 # Short-term (DB) + long-term (ChromaDB) memory
├── rag/                    # PDF ingestion, chunking, vector retrieval
├── services/               # Business logic (analysis, chat, portfolio, risk)
├── tools/                  # LangChain tools wrapping financial APIs
├── websocket/              # WebSocket connection manager
├── tests/                  # pytest test suite
├── migrations/             # Alembic migration scripts
├── main.py                 # Application factory
├── config.py               # Centralized settings
├── requirements.txt
└── docker-compose.yml
```

## Key Design Decisions

### Why LangGraph over plain LangChain?
LangGraph provides explicit state management and conditional routing between agents.
The investment workflow is inherently stateful — each agent reads from and writes to
a shared `InvestmentAnalysisState` TypedDict. LangGraph makes this explicit and
debuggable, versus hidden state in LangChain chains.

### Why Repository Pattern?
Routes → Services → Repositories. Routes stay thin (validation + auth), services contain business logic,
repositories contain SQL. This makes services testable without a real DB, and makes
it easy to swap PostgreSQL for another store if needed.

### Why dual memory (PostgreSQL + ChromaDB)?
PostgreSQL for structured, relational conversation history (queryable, ACID).
ChromaDB for semantic/vector memory — "what did this user care about 3 weeks ago?"
is a semantic search problem, not a SQL problem.

### Why rule-based fallback in StrategyAgent?
LLM API calls can fail, be slow, or be expensive. The rule-based fallback ensures
the API always returns a recommendation even if OpenAI is down, making the system
resilient and cost-controllable.
