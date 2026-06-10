"""
services/analysis_service.py — Stock/crypto analysis orchestration service.

Bridges API routes → LangGraph workflow → response schemas.
Also handles caching to avoid redundant analyses.
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from core.logging import logger
from langgraph_workflow.graph import get_investment_graph, InvestmentAnalysisState
from schemas.schemas import (
    StockAnalysisRequest, CryptoAnalysisRequest,
    StockAnalysisResponse, TechnicalIndicators, InvestmentRecommendation,
)


class AnalysisService:
    """Orchestrates the full analysis workflow and handles result caching."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._redis = None

    async def analyze_stock(
        self,
        symbol: str,
        user_id: str,
        user_risk_tolerance: str,
        request: StockAnalysisRequest,
    ) -> StockAnalysisResponse:
        """Run full multi-agent stock analysis via LangGraph."""
        # Check cache first
        cache_key = self._make_cache_key("stock", symbol, request.period)
        cached = await self._get_cached(cache_key)
        if cached:
            logger.info("Returning cached analysis", symbol=symbol)
            return StockAnalysisResponse(**cached)

        # Run LangGraph workflow
        initial_state: InvestmentAnalysisState = {
            "symbol": symbol,
            "asset_type": "stock",
            "user_id": user_id,
            "user_risk_tolerance": user_risk_tolerance,
            "period": request.period,
            "include_news": request.include_news,
            "include_sentiment": request.include_sentiment,
            "include_technical": request.include_technical,
            "portfolio_context": None,
            "session_id": None,
            "memory_context": None,
            "financial_data": None,
            "news_data": None,
            "sentiment_data": None,
            "risk_data": None,
            "recommendation": None,
            "reasoning_summary": None,
            "agent_steps": [],
            "error": None,
            "completed_at": None,
        }

        graph = get_investment_graph()
        final_state = await graph.ainvoke(initial_state)

        response = self._build_response(symbol, final_state)

        # Cache for 5 minutes
        await self._set_cached(cache_key, response.model_dump(mode="json"), ttl_minutes=5)
        return response

    async def analyze_crypto(
        self,
        symbol: str,
        user_id: str,
        user_risk_tolerance: str,
        request: CryptoAnalysisRequest,
    ) -> StockAnalysisResponse:
        """Run full multi-agent crypto analysis via LangGraph."""
        cache_key = self._make_cache_key("crypto", symbol, str(request.days))
        cached = await self._get_cached(cache_key)
        if cached:
            return StockAnalysisResponse(**cached)

        initial_state: InvestmentAnalysisState = {
            "symbol": symbol.upper(),
            "asset_type": "crypto",
            "user_id": user_id,
            "user_risk_tolerance": user_risk_tolerance,
            "period": f"{request.days}d",
            "include_news": True,
            "include_sentiment": request.include_sentiment,
            "include_technical": True,
            "portfolio_context": None,
            "session_id": None,
            "memory_context": None,
            "financial_data": None,
            "news_data": None,
            "sentiment_data": None,
            "risk_data": None,
            "recommendation": None,
            "reasoning_summary": None,
            "agent_steps": [],
            "error": None,
            "completed_at": None,
        }

        graph = get_investment_graph()
        final_state = await graph.ainvoke(initial_state)

        response = self._build_response(symbol, final_state)
        await self._set_cached(cache_key, response.model_dump(mode="json"), ttl_minutes=3)
        return response

    def _build_response(self, symbol: str, state: InvestmentAnalysisState) -> StockAnalysisResponse:
        """Convert final graph state into API response schema."""
        financial = state.get("financial_data") or {}
        sentiment = state.get("sentiment_data") or {}
        news = state.get("news_data") or {}
        rec_data = state.get("recommendation") or {}
        tech = financial.get("technical_data") or {}
        price = financial.get("price_data") or {}

        # Build TechnicalIndicators
        tech_indicators = None
        if tech and not tech.get("error"):
            tech_indicators = TechnicalIndicators(
                rsi=tech.get("rsi"),
                macd=tech.get("macd"),
                macd_signal=tech.get("macd_signal"),
                macd_histogram=tech.get("macd_histogram"),
                sma_20=tech.get("sma_20"),
                sma_50=tech.get("sma_50"),
                ema_20=tech.get("ema_20"),
                bollinger_upper=tech.get("bollinger_upper"),
                bollinger_lower=tech.get("bollinger_lower"),
                atr=tech.get("atr"),
                volume_sma=tech.get("volume_sma"),
            )

        # Build InvestmentRecommendation
        recommendation = None
        if rec_data and rec_data.get("action"):
            recommendation = InvestmentRecommendation(
                action=rec_data["action"],
                confidence=rec_data.get("confidence", 0.5),
                reasoning=rec_data.get("reasoning", ""),
                risk_level=rec_data.get("risk_level", "medium"),
                time_horizon=rec_data.get("time_horizon", "medium"),
                price_targets=rec_data.get("price_targets", {}),
                risk_factors=rec_data.get("risk_factors", []),
                supporting_factors=rec_data.get("supporting_factors", []),
            )

        # Combine agent reasoning steps
        agent_steps = state.get("agent_steps", [])
        reasoning_summary = state.get("reasoning_summary")

        return StockAnalysisResponse(
            symbol=symbol.upper(),
            company_name=price.get("company_name"),
            current_price=price.get("current_price"),
            price_change_24h=price.get("change"),
            price_change_pct_24h=price.get("change_pct"),
            market_cap=price.get("market_cap"),
            volume=price.get("volume"),
            technical_indicators=tech_indicators,
            news_summary=news.get("news_summary"),
            sentiment_score=sentiment.get("sentiment_score"),
            sentiment_label=sentiment.get("sentiment_label"),
            recommendation=recommendation,
            analysis_timestamp=datetime.utcnow(),
            agent_reasoning=reasoning_summary,
        )

    # ─── Cache Helpers ────────────────────────────────────────────────────────

    def _make_cache_key(self, analysis_type: str, symbol: str, param: str) -> str:
        raw = f"{analysis_type}:{symbol}:{param}"
        return hashlib.md5(raw.encode()).hexdigest()

    async def _get_cached(self, cache_key: str) -> Optional[dict]:
        """Check Redis first, then PostgreSQL cache."""
        redis_client = await self._get_redis()
        if redis_client is not None:
            try:
                cached = await redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.debug("Redis cache read failed", error=str(e))

        try:
            from sqlalchemy import select
            from database.models.models import AnalysisCache
            result = await self.db.execute(
                select(AnalysisCache).where(
                    AnalysisCache.cache_key == cache_key,
                    AnalysisCache.expires_at > datetime.utcnow(),
                )
            )
            cached = result.scalar_one_or_none()
            if cached:
                return cached.result
        except Exception as e:
            logger.debug("Cache miss or error", error=str(e))
        return None

    async def _set_cached(self, cache_key: str, data: dict, ttl_minutes: int = 5) -> None:
        """Store analysis result in Redis when available and PostgreSQL fallback."""
        redis_client = await self._get_redis()
        if redis_client is not None:
            try:
                await redis_client.set(
                    cache_key,
                    json.dumps(data),
                    ex=ttl_minutes * 60,
                )
            except Exception as e:
                logger.debug("Redis cache write failed", error=str(e))

        try:
            from database.models.models import AnalysisCache
            from sqlalchemy.dialects.postgresql import insert

            expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)

            # Upsert: update if exists, insert if not
            from sqlalchemy import update, select
            existing = await self.db.execute(
                select(AnalysisCache).where(AnalysisCache.cache_key == cache_key)
            )
            cached = existing.scalar_one_or_none()
            if cached:
                cached.result = data
                cached.expires_at = expires_at
            else:
                self.db.add(AnalysisCache(
                    cache_key=cache_key,
                    analysis_type="stock",
                    symbol="",
                    result=data,
                    expires_at=expires_at,
                ))
            await self.db.flush()
        except Exception as e:
            logger.debug("Cache write failed", error=str(e))

    async def _get_redis(self):
        """Return a Redis client when reachable; otherwise fall back silently."""
        if self._redis is not None:
            return self._redis

        try:
            import redis.asyncio as redis

            client = redis.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
                decode_responses=True,
            )
            await client.ping()
            self._redis = client
            return self._redis
        except Exception as e:
            logger.debug("Redis unavailable, using database cache fallback", error=str(e))
            return None
