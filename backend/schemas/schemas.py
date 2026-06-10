"""schemas/schemas.py — All Pydantic v2 request/response schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=200)
    risk_tolerance: Optional[str] = Field(default="moderate")

    @field_validator("risk_tolerance")
    @classmethod
    def validate_risk_tolerance(cls, v):
        if v and v not in {"conservative", "moderate", "aggressive"}:
            raise ValueError("Must be conservative, moderate, or aggressive")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    risk_tolerance: Optional[str]
    created_at: datetime


class CreatePortfolioRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    initial_cash: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="USD", max_length=10)


class AddHoldingRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    asset_type: str = Field(default="stock")
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    notes: Optional[str] = None

    @field_validator("symbol")
    @classmethod
    def upper_symbol(cls, v): return v.upper()

    @field_validator("asset_type")
    @classmethod
    def validate_type(cls, v):
        if v not in {"stock", "crypto", "etf", "bond"}:
            raise ValueError("Invalid asset type")
        return v


class HoldingResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    symbol: str
    asset_type: str
    quantity: Decimal
    average_buy_price: Decimal
    current_price: Optional[Decimal]
    unrealized_pnl: Optional[Decimal] = None
    unrealized_pnl_pct: Optional[Decimal] = None


class PortfolioResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    name: str
    description: Optional[str]
    cash_balance: Decimal
    currency: str
    is_default: bool
    holdings: list[HoldingResponse] = []
    total_value: Optional[Decimal] = None
    created_at: datetime


class TransactionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    symbol: str
    asset_type: str
    transaction_type: str
    quantity: Decimal
    price: Decimal
    total_value: Decimal
    fees: Decimal
    executed_at: datetime


class AddWatchlistRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    asset_type: str = Field(default="stock")
    notes: Optional[str] = None
    alert_price_above: Optional[Decimal] = Field(default=None, gt=0)
    alert_price_below: Optional[Decimal] = Field(default=None, gt=0)

    @field_validator("symbol")
    @classmethod
    def upper_symbol(cls, v): return v.upper()


class WatchlistResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    symbol: str
    asset_type: str
    notes: Optional[str]
    alert_price_above: Optional[Decimal]
    alert_price_below: Optional[Decimal]
    created_at: datetime


class StockAnalysisRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    period: str = Field(default="1y")
    include_technical: bool = True
    include_fundamental: bool = True
    include_news: bool = True
    include_sentiment: bool = True

    @field_validator("symbol")
    @classmethod
    def upper_symbol(cls, v): return v.upper()


class CryptoAnalysisRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    vs_currency: str = Field(default="usd")
    days: int = Field(default=30, ge=1, le=365)
    include_sentiment: bool = True


class TechnicalIndicators(BaseModel):
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_20: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    atr: Optional[float] = None
    volume_sma: Optional[float] = None


class InvestmentRecommendation(BaseModel):
    action: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    risk_level: str
    time_horizon: str
    price_targets: dict[str, Optional[float]] = {}
    risk_factors: list[str] = []
    supporting_factors: list[str] = []


class StockAnalysisResponse(BaseModel):
    symbol: str
    company_name: Optional[str]
    current_price: Optional[float]
    price_change_24h: Optional[float]
    price_change_pct_24h: Optional[float]
    market_cap: Optional[float]
    volume: Optional[float]
    technical_indicators: Optional[TechnicalIndicators]
    news_summary: Optional[str]
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    recommendation: Optional[InvestmentRecommendation]
    analysis_timestamp: datetime
    agent_reasoning: Optional[str] = None


class NewsArticle(BaseModel):
    title: str
    description: Optional[str]
    url: str
    source: str
    published_at: Optional[datetime]
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    summary: Optional[str]


class NewsResponse(BaseModel):
    articles: list[NewsArticle]
    total_count: int
    bullish_count: int
    bearish_count: int
    neutral_count: int
    overall_sentiment: str
    query: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    session_id: Optional[str] = None
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    agent_steps: Optional[list[str]] = None
    tools_used: Optional[list[str]] = None
    timestamp: datetime


class RiskAnalysisRequest(BaseModel):
    portfolio_id: Optional[str] = None
    symbols: Optional[list[str]] = None

    @model_validator(mode="after")
    def validate_input(self):
        if not self.portfolio_id and not self.symbols:
            raise ValueError("Either portfolio_id or symbols must be provided")
        return self


class RiskMetrics(BaseModel):
    volatility_30d: Optional[float]
    beta: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    var_95: Optional[float]
    concentration_risk: Optional[float]
    diversification_score: Optional[float]


class RiskAnalysisResponse(BaseModel):
    risk_score: float = Field(ge=0.0, le=10.0)
    risk_level: str
    metrics: RiskMetrics
    risk_factors: list[str]
    recommendations: list[str]
    analysis_timestamp: datetime


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    status: str


class RAGQueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    document_ids: Optional[list[str]] = None


class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    confidence: float
    query: str
