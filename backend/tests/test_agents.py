"""
tests/test_agents.py — Unit tests for individual AI agents.

Uses mocking to avoid real API calls in tests.
Each agent is tested for correct output structure and edge case handling.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ─── Financial Agent ──────────────────────────────────────────────────────────

class TestFinancialAgent:
    @pytest.mark.asyncio
    async def test_run_returns_expected_keys(self):
        from agents.financial_agent import FinancialAgent

        mock_price = {"current_price": 175.5, "company_name": "Apple Inc.", "change_pct": 1.2}
        mock_tech = {"rsi": 55.0, "macd": 0.5, "signals": ["RSI neutral (55.0)"]}
        mock_vol = {"volatility_annual": 0.25, "beta": 1.1, "max_drawdown": -0.15}

        with patch("agents.financial_agent.get_stock_price_tool", new=AsyncMock(return_value=mock_price)), \
             patch("agents.financial_agent.calculate_technical_indicators", new=AsyncMock(return_value=mock_tech)), \
             patch("agents.financial_agent.calculate_volatility", new=AsyncMock(return_value=mock_vol)):

            agent = FinancialAgent()
            result = await agent.run("AAPL", "stock")

        assert result["symbol"] == "AAPL"
        assert result["agent"] == "financial"
        assert "price_data" in result
        assert "technical_data" in result
        assert "volatility_data" in result
        assert isinstance(result["signals"], list)

    @pytest.mark.asyncio
    async def test_handles_api_error_gracefully(self):
        from agents.financial_agent import FinancialAgent

        with patch("agents.financial_agent.get_stock_price_tool", new=AsyncMock(side_effect=Exception("API timeout"))), \
             patch("agents.financial_agent.calculate_technical_indicators", new=AsyncMock(return_value={})), \
             patch("agents.financial_agent.calculate_volatility", new=AsyncMock(return_value={})):

            agent = FinancialAgent()
            result = await agent.run("INVALID", "stock")

        # Should not raise — gracefully returns partial data
        assert "symbol" in result


# ─── Sentiment Agent ──────────────────────────────────────────────────────────

class TestSentimentAgent:
    @pytest.mark.asyncio
    async def test_bullish_sentiment(self):
        from agents.sentiment_agent import SentimentAgent

        news_data = {
            "overall_sentiment": "bullish",
            "bullish_ratio": 0.75,
            "bullish_count": 15,
            "bearish_count": 3,
            "neutral_count": 2,
        }
        financial_data = {
            "technical_data": {"rsi": 45.0, "macd": 0.8, "macd_signal": 0.3},
            "volatility_data": {"volatility_annual": 0.2},
        }

        agent = SentimentAgent()
        result = await agent.run("AAPL", news_data, financial_data)

        assert result["agent"] == "sentiment"
        assert result["sentiment_label"] in ("bullish", "neutral", "bearish")
        assert -1.0 <= result["sentiment_score"] <= 1.0
        assert 0.0 <= result["confidence"] <= 1.0
        assert isinstance(result["explanations"], list)

    @pytest.mark.asyncio
    async def test_bearish_rsi_overbought(self):
        from agents.sentiment_agent import SentimentAgent

        news_data = {"overall_sentiment": "neutral", "bullish_ratio": 0.5,
                     "bullish_count": 5, "bearish_count": 5, "neutral_count": 0}
        financial_data = {
            "technical_data": {"rsi": 78.0, "macd": -0.2, "macd_signal": 0.1},
            "volatility_data": {"volatility_annual": 0.35},
        }

        agent = SentimentAgent()
        result = await agent.run("OVERBOUGHT", news_data, financial_data)

        # High RSI + bearish MACD should push toward bearish
        assert result["sentiment_score"] < 0.25
        assert any("overbought" in e.lower() or "RSI" in e for e in result["explanations"])

    @pytest.mark.asyncio
    async def test_oversold_bullish_signal(self):
        from agents.sentiment_agent import SentimentAgent

        news_data = {"overall_sentiment": "bearish", "bullish_ratio": 0.2,
                     "bullish_count": 2, "bearish_count": 8, "neutral_count": 0}
        financial_data = {
            "technical_data": {"rsi": 22.0, "macd": 0.1, "macd_signal": -0.2},
            "volatility_data": {"volatility_annual": 0.3},
        }

        agent = SentimentAgent()
        result = await agent.run("OVERSOLD", news_data, financial_data)

        # Oversold RSI should generate a reversal signal
        assert any("oversold" in e.lower() or "reversal" in e.lower() for e in result["explanations"])


# ─── Risk Agent ───────────────────────────────────────────────────────────────

class TestRiskAgent:
    @pytest.mark.asyncio
    async def test_low_risk_stock(self):
        from agents.risk_agent import RiskAgent

        mock_vol = {
            "volatility_annual": 0.12,
            "beta": 0.7,
            "max_drawdown": -0.08,
            "sharpe_ratio": 1.8,
        }
        with patch("agents.risk_agent.calculate_volatility", new=AsyncMock(return_value=mock_vol)):
            agent = RiskAgent()
            result = await agent.run("JNJ")

        assert result["risk_level"] == "low"
        assert result["risk_score"] <= 3.0
        assert result["agent"] == "risk"

    @pytest.mark.asyncio
    async def test_high_risk_volatile_stock(self):
        from agents.risk_agent import RiskAgent

        mock_vol = {
            "volatility_annual": 0.75,
            "beta": 2.3,
            "max_drawdown": -0.55,
            "sharpe_ratio": 0.3,
        }
        with patch("agents.risk_agent.calculate_volatility", new=AsyncMock(return_value=mock_vol)):
            agent = RiskAgent()
            result = await agent.run("HIGHVOL")

        assert result["risk_level"] in ("high", "very_high")
        assert result["risk_score"] >= 6.0
        assert len(result["risk_factors"]) >= 2

    @pytest.mark.asyncio
    async def test_handles_missing_beta(self):
        from agents.risk_agent import RiskAgent

        mock_vol = {"volatility_annual": 0.25, "beta": None, "max_drawdown": -0.2, "sharpe_ratio": None}
        with patch("agents.risk_agent.calculate_volatility", new=AsyncMock(return_value=mock_vol)):
            result = await RiskAgent().run("NOBETA")

        assert "risk_level" in result
        assert result["beta"] is None


# ─── Strategy Agent ───────────────────────────────────────────────────────────

class TestStrategyAgent:
    @pytest.mark.asyncio
    async def test_rule_based_buy_signal(self):
        from agents.strategy_agent import StrategyAgent

        agent = StrategyAgent()
        result = agent._rule_based_recommendation(
            symbol="AAPL",
            financial_data={"technical_data": {"rsi": 42.0, "macd": 0.8, "macd_signal": 0.3}, "signals": []},
            news_data={"overall_sentiment": "bullish", "bullish_ratio": 0.75,
                       "bullish_count": 15, "bearish_count": 3, "neutral_count": 2},
            sentiment_data={"sentiment_score": 0.65, "sentiment_label": "bullish", "confidence": 0.7},
            risk_data={"risk_level": "medium", "risk_score": 4.0, "risk_factors": []},
            user_risk_tolerance="moderate",
        )

        assert result["action"] == "BUY"
        assert result["confidence"] > 0.5
        assert result["agent"] == "strategy"

    @pytest.mark.asyncio
    async def test_rule_based_sell_signal(self):
        from agents.strategy_agent import StrategyAgent

        agent = StrategyAgent()
        result = agent._rule_based_recommendation(
            symbol="CRASH",
            financial_data={"technical_data": {"rsi": 78.0, "macd": -1.2, "macd_signal": -0.3}, "signals": []},
            news_data={"overall_sentiment": "bearish", "bullish_ratio": 0.1,
                       "bullish_count": 1, "bearish_count": 9, "neutral_count": 0},
            sentiment_data={"sentiment_score": -0.8, "sentiment_label": "bearish", "confidence": 0.9},
            risk_data={"risk_level": "high", "risk_score": 7.5, "risk_factors": ["High volatility"]},
            user_risk_tolerance="conservative",
        )

        assert result["action"] == "SELL"

    @pytest.mark.asyncio
    async def test_conservative_user_dampens_high_risk(self):
        from agents.strategy_agent import StrategyAgent

        agent = StrategyAgent()
        result = agent._rule_based_recommendation(
            symbol="RISKY",
            financial_data={"technical_data": {"rsi": 55.0, "macd": 0.5, "macd_signal": 0.2}, "signals": []},
            news_data={"overall_sentiment": "bullish", "bullish_ratio": 0.65,
                       "bullish_count": 13, "bearish_count": 4, "neutral_count": 3},
            sentiment_data={"sentiment_score": 0.4, "sentiment_label": "bullish", "confidence": 0.6},
            risk_data={"risk_level": "high", "risk_score": 7.0, "risk_factors": ["High volatility", "High beta"]},
            user_risk_tolerance="conservative",
        )

        # Conservative user + high risk → confidence should be dampened
        assert result["confidence"] <= 0.6


# ─── Memory Manager ───────────────────────────────────────────────────────────

class TestMemoryManager:
    @pytest.mark.asyncio
    async def test_heuristic_sentiment_bullish(self):
        from services.sentiment_service import SentimentService
        svc = SentimentService()
        result = svc._heuristic_sentiment("Strong buy signal, stock surging to record highs with massive gains and profits")
        assert result["label"] == "positive"
        assert result["score"] > 0.5

    @pytest.mark.asyncio
    async def test_heuristic_sentiment_bearish(self):
        from services.sentiment_service import SentimentService
        svc = SentimentService()
        result = svc._heuristic_sentiment("Stock crashes, massive losses, recession fears, sell everything bear market")
        assert result["label"] == "negative"
        assert result["score"] > 0.5

    @pytest.mark.asyncio
    async def test_heuristic_sentiment_empty_text(self):
        from services.sentiment_service import SentimentService
        svc = SentimentService()
        result = svc._heuristic_sentiment("")
        assert result["label"] == "neutral"


# ─── RAG Pipeline ─────────────────────────────────────────────────────────────

class TestRAGPipeline:
    def test_chunk_text_basic(self):
        from rag.pipeline import RAGPipeline
        pipeline = RAGPipeline()
        text = "First paragraph about revenue.\n\nSecond paragraph about expenses.\n\nThird paragraph about growth."
        chunks = pipeline._chunk_text(text)
        assert len(chunks) >= 1
        assert all(len(c) > 10 for c in chunks)

    def test_chunk_text_long_document(self):
        from rag.pipeline import RAGPipeline
        pipeline = RAGPipeline()
        # Generate text longer than chunk size
        long_text = "\n\n".join([f"Paragraph {i}: " + "Financial data. " * 50 for i in range(20)])
        chunks = pipeline._chunk_text(long_text)
        # Should produce multiple chunks
        assert len(chunks) > 1
        # No chunk should massively exceed CHUNK_SIZE
        for chunk in chunks:
            assert len(chunk) <= pipeline.CHUNK_SIZE + pipeline.CHUNK_OVERLAP + 200

    def test_chunk_text_short_document(self):
        from rag.pipeline import RAGPipeline
        pipeline = RAGPipeline()
        short = "Short document."
        chunks = pipeline._chunk_text(short)
        # Short text filtered out (< 50 chars)
        assert len(chunks) == 0 or chunks[0] == short
