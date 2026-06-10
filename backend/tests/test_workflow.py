"""
tests/test_workflow.py — Integration tests for the LangGraph multi-agent workflow.

Tests the full state machine from initial state through all nodes
to final recommendation output, using mocked agent calls.
"""

import pytest
from unittest.mock import AsyncMock, patch


MOCK_PRICE_DATA = {
    "current_price": 175.5,
    "company_name": "Apple Inc.",
    "change_pct": 1.5,
    "market_cap": 2_700_000_000_000,
    "volume": 52_000_000,
}

MOCK_TECH_DATA = {
    "rsi": 52.0,
    "macd": 0.45,
    "macd_signal": 0.30,
    "sma_20": 172.0,
    "sma_50": 168.0,
    "signals": ["RSI neutral (52.0)", "MACD bullish crossover"],
    "current_price": 175.5,
}

MOCK_VOL_DATA = {
    "volatility_annual": 0.28,
    "beta": 1.15,
    "max_drawdown": -0.18,
    "sharpe_ratio": 0.95,
}

MOCK_NEWS_DATA = {
    "symbol": "AAPL",
    "overall_sentiment": "bullish",
    "bullish_count": 12,
    "bearish_count": 3,
    "neutral_count": 5,
    "bullish_ratio": 0.6,
    "news_summary": "Overall news sentiment: bullish\n12 bullish, 3 bearish articles.",
    "articles": [],
    "agent": "news",
}


def test_graph_node_names_do_not_conflict_with_state_keys():
    """Graph node names must stay distinct from state fields."""
    from langgraph_workflow.graph import _state_keys, _validate_node_names

    node_names = {
        "planner",
        "memory_retrieval",
        "financial",
        "news",
        "sentiment",
        "risk",
        "reasoning",
        "recommendation_agent",
        "memory_store",
    }

    assert not (node_names & _state_keys())

    with pytest.raises(ValueError, match="recommendation"):
        _validate_node_names(["recommendation"])


@pytest.mark.asyncio
async def test_full_workflow_returns_recommendation():
    """End-to-end workflow test with mocked external API calls."""
    from langgraph_workflow.graph import get_investment_graph, InvestmentAnalysisState

    with patch("agents.financial_agent.get_stock_price_tool", new=AsyncMock(return_value=MOCK_PRICE_DATA)), \
         patch("agents.financial_agent.calculate_technical_indicators", new=AsyncMock(return_value=MOCK_TECH_DATA)), \
         patch("agents.financial_agent.calculate_volatility", new=AsyncMock(return_value=MOCK_VOL_DATA)), \
         patch("agents.news_agent.NewsService") as MockNews, \
         patch("agents.risk_agent.calculate_volatility", new=AsyncMock(return_value=MOCK_VOL_DATA)), \
         patch("memory.memory_manager.MemoryManager.retrieve_relevant_memory", new=AsyncMock(return_value=[])), \
         patch("memory.memory_manager.MemoryManager.store_long_term", new=AsyncMock()):

        # Mock NewsService
        from schemas.schemas import NewsResponse
        mock_news_instance = MockNews.return_value
        mock_news_instance.get_analyzed_news = AsyncMock(return_value=NewsResponse(
            articles=[], total_count=20, bullish_count=12, bearish_count=3,
            neutral_count=5, overall_sentiment="bullish", query="AAPL"
        ))

        initial_state: InvestmentAnalysisState = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "user_id": "test-user-123",
            "user_risk_tolerance": "moderate",
            "period": "1y",
            "include_news": True,
            "include_sentiment": True,
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

    # Validate final state structure
    assert final_state["symbol"] == "AAPL"
    assert final_state["financial_data"] is not None
    assert final_state["recommendation"] is not None
    assert final_state["recommendation"]["action"] in ("BUY", "HOLD", "SELL")
    assert 0.0 <= final_state["recommendation"]["confidence"] <= 1.0
    assert final_state["recommendation"]["reasoning"]
    assert len(final_state["agent_steps"]) > 0
    assert final_state["completed_at"] is not None


@pytest.mark.asyncio
async def test_workflow_agent_steps_recorded():
    """All nodes should append their step to agent_steps."""
    from langgraph_workflow.graph import get_investment_graph, InvestmentAnalysisState

    with patch("agents.financial_agent.get_stock_price_tool", new=AsyncMock(return_value=MOCK_PRICE_DATA)), \
         patch("agents.financial_agent.calculate_technical_indicators", new=AsyncMock(return_value=MOCK_TECH_DATA)), \
         patch("agents.financial_agent.calculate_volatility", new=AsyncMock(return_value=MOCK_VOL_DATA)), \
         patch("agents.news_agent.NewsService") as MockNews, \
         patch("agents.risk_agent.calculate_volatility", new=AsyncMock(return_value=MOCK_VOL_DATA)), \
         patch("memory.memory_manager.MemoryManager.retrieve_relevant_memory", new=AsyncMock(return_value=[])), \
         patch("memory.memory_manager.MemoryManager.store_long_term", new=AsyncMock()):

        from schemas.schemas import NewsResponse
        MockNews.return_value.get_analyzed_news = AsyncMock(return_value=NewsResponse(
            articles=[], total_count=5, bullish_count=3, bearish_count=1,
            neutral_count=1, overall_sentiment="bullish", query="MSFT"
        ))

        initial_state: InvestmentAnalysisState = {
            "symbol": "MSFT", "asset_type": "stock", "user_id": "user-456",
            "user_risk_tolerance": "aggressive", "period": "6mo",
            "include_news": True, "include_sentiment": True, "include_technical": True,
            "portfolio_context": None, "session_id": None, "memory_context": None,
            "financial_data": None, "news_data": None, "sentiment_data": None,
            "risk_data": None, "recommendation": None, "reasoning_summary": None,
            "agent_steps": [], "error": None, "completed_at": None,
        }

        graph = get_investment_graph()
        final_state = await graph.ainvoke(initial_state)

    steps = final_state["agent_steps"]
    assert len(steps) >= 5  # planner, memory, financial, news, sentiment, risk, reasoning, recommendation
    step_text = " ".join(steps).lower()
    assert "planner" in step_text
    assert "financial" in step_text or "aapl" in step_text or "msft" in step_text
    assert "recommendation" in step_text


@pytest.mark.asyncio
async def test_workflow_handles_news_failure_gracefully():
    """If NewsAgent fails, workflow should continue with neutral news data."""
    from langgraph_workflow.graph import get_investment_graph, InvestmentAnalysisState

    with patch("agents.financial_agent.get_stock_price_tool", new=AsyncMock(return_value=MOCK_PRICE_DATA)), \
         patch("agents.financial_agent.calculate_technical_indicators", new=AsyncMock(return_value=MOCK_TECH_DATA)), \
         patch("agents.financial_agent.calculate_volatility", new=AsyncMock(return_value=MOCK_VOL_DATA)), \
         patch("agents.news_agent.NewsService") as MockNews, \
         patch("agents.risk_agent.calculate_volatility", new=AsyncMock(return_value=MOCK_VOL_DATA)), \
         patch("memory.memory_manager.MemoryManager.retrieve_relevant_memory", new=AsyncMock(return_value=[])), \
         patch("memory.memory_manager.MemoryManager.store_long_term", new=AsyncMock()):

        MockNews.return_value.get_analyzed_news = AsyncMock(side_effect=Exception("News API down"))

        initial_state: InvestmentAnalysisState = {
            "symbol": "GOOG", "asset_type": "stock", "user_id": "user-789",
            "user_risk_tolerance": "moderate", "period": "1y",
            "include_news": True, "include_sentiment": True, "include_technical": True,
            "portfolio_context": None, "session_id": None, "memory_context": None,
            "financial_data": None, "news_data": None, "sentiment_data": None,
            "risk_data": None, "recommendation": None, "reasoning_summary": None,
            "agent_steps": [], "error": None, "completed_at": None,
        }

        graph = get_investment_graph()
        final_state = await graph.ainvoke(initial_state)

    # Workflow should complete despite news failure
    assert final_state["recommendation"] is not None
    assert final_state["recommendation"]["action"] in ("BUY", "HOLD", "SELL")


@pytest.mark.asyncio
async def test_workflow_conservative_user_gets_appropriate_recommendation():
    """Conservative risk tolerance should dampen aggressive BUY signals."""
    from langgraph_workflow.graph import get_investment_graph, InvestmentAnalysisState

    high_vol_data = {**MOCK_VOL_DATA, "volatility_annual": 0.65, "beta": 2.1, "max_drawdown": -0.45}

    with patch("agents.financial_agent.get_stock_price_tool", new=AsyncMock(return_value=MOCK_PRICE_DATA)), \
         patch("agents.financial_agent.calculate_technical_indicators", new=AsyncMock(return_value=MOCK_TECH_DATA)), \
         patch("agents.financial_agent.calculate_volatility", new=AsyncMock(return_value=high_vol_data)), \
         patch("agents.news_agent.NewsService") as MockNews, \
         patch("agents.risk_agent.calculate_volatility", new=AsyncMock(return_value=high_vol_data)), \
         patch("memory.memory_manager.MemoryManager.retrieve_relevant_memory", new=AsyncMock(return_value=[])), \
         patch("memory.memory_manager.MemoryManager.store_long_term", new=AsyncMock()):

        from schemas.schemas import NewsResponse
        MockNews.return_value.get_analyzed_news = AsyncMock(return_value=NewsResponse(
            articles=[], total_count=5, bullish_count=5, bearish_count=0,
            neutral_count=0, overall_sentiment="bullish", query="VOLATILE"
        ))

        initial_state: InvestmentAnalysisState = {
            "symbol": "VOLATILE", "asset_type": "stock", "user_id": "conservative-user",
            "user_risk_tolerance": "conservative", "period": "1y",
            "include_news": True, "include_sentiment": True, "include_technical": True,
            "portfolio_context": None, "session_id": None, "memory_context": None,
            "financial_data": None, "news_data": None, "sentiment_data": None,
            "risk_data": None, "recommendation": None, "reasoning_summary": None,
            "agent_steps": [], "error": None, "completed_at": None,
        }

        graph = get_investment_graph()
        final_state = await graph.ainvoke(initial_state)

    rec = final_state["recommendation"]
    assert rec is not None
    # High-volatility stock for conservative user → confidence should be low
    # or recommendation should not be a strong BUY
    if rec["action"] == "BUY":
        assert rec["confidence"] < 0.75  # Dampened confidence
