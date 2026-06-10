"""
langgraph_workflow/graph.py — Multi-agent LangGraph workflow.

Graph topology:
    START
      │
      ▼
  [planner_node]  — decides which agents to run based on request type
      │
      ├──────────────────────────────────────────────────┐
      ▼                                                  ▼
  [memory_node]                                   (parallel fanout)
      │               ┌──────────────┬────────────────────────────┐
      ▼               ▼              ▼            ▼               ▼
  [financial_node] [news_node] [sentiment_node] [risk_node]  (join)
      │               │              │            │
      └───────────────┴──────────────┴────────────┘
                                │
                                ▼
                       [reasoning_node]  — aggregates all outputs
                                │
                                ▼
                     [recommendation_node] — final BUY/HOLD/SELL
                                │
                                ▼
                       [memory_store_node] — persist result
                                │
                                ▼
                             END

State is a TypedDict flowing through all nodes.
Conditional edges enable retries and skip-ahead paths.
"""

import asyncio
from typing import TypedDict, Optional, Annotated, Iterable
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from core.logging import logger
from agents.financial_agent import FinancialAgent
from agents.news_agent import NewsAgent
from agents.sentiment_agent import SentimentAgent
from agents.risk_agent import RiskAgent
from agents.strategy_agent import StrategyAgent
from agents.memory_agent import MemoryAgent


# ─── Graph State ──────────────────────────────────────────────────────────────

class InvestmentAnalysisState(TypedDict):
    """
    Shared state that flows through all nodes in the graph.
    Each node reads from and writes to this state dict.
    """
    # Inputs
    symbol: str
    asset_type: str
    user_id: str
    user_risk_tolerance: str
    period: str
    include_news: bool
    include_sentiment: bool
    include_technical: bool
    portfolio_context: Optional[dict]
    session_id: Optional[str]

    # Intermediate agent outputs
    memory_context: Optional[dict]
    financial_data: Optional[dict]
    news_data: Optional[dict]
    sentiment_data: Optional[dict]
    risk_data: Optional[dict]

    # Final outputs
    recommendation: Optional[dict]
    reasoning_summary: Optional[str]
    agent_steps: list[str]
    error: Optional[str]
    completed_at: Optional[str]


# ─── Node Implementations ─────────────────────────────────────────────────────

async def planner_node(state: InvestmentAnalysisState) -> InvestmentAnalysisState:
    """
    Plans the analysis workflow.
    In more complex scenarios, this could dynamically decide which agents
    to invoke based on the symbol type, available data, or user preferences.
    """
    logger.info("Planner node", symbol=state["symbol"])
    steps = state.get("agent_steps", [])
    steps.append(f"Planner: analyzing {state['symbol']} ({state['asset_type']})")
    return {**state, "agent_steps": steps}


async def memory_retrieval_node(state: InvestmentAnalysisState) -> InvestmentAnalysisState:
    """Retrieve relevant user memories before running analysis."""
    try:
        agent = MemoryAgent()
        memory_ctx = await agent.retrieve_context(
            user_id=state["user_id"],
            query=f"investment analysis {state['symbol']}",
        )
        steps = state.get("agent_steps", [])
        steps.append(f"Memory: retrieved {len(memory_ctx.get('user_preferences', []))} relevant memories")
        return {**state, "memory_context": memory_ctx, "agent_steps": steps}
    except Exception as e:
        logger.warning("Memory retrieval failed, continuing", error=str(e))
        return {**state, "memory_context": {}}


async def financial_node(state: InvestmentAnalysisState) -> InvestmentAnalysisState:
    """Run financial data analysis agent."""
    try:
        agent = FinancialAgent()
        financial_data = await agent.run(
            symbol=state["symbol"],
            asset_type=state["asset_type"],
            period=state["period"],
        )
        steps = state.get("agent_steps", [])
        steps.append(f"Financial: {len(financial_data.get('signals', []))} signals detected")
        return {**state, "financial_data": financial_data, "agent_steps": steps}
    except Exception as e:
        logger.error("Financial node failed", error=str(e))
        return {**state, "financial_data": {"error": str(e), "signals": []},
                "error": f"Financial data error: {str(e)}"}


async def news_node(state: InvestmentAnalysisState) -> InvestmentAnalysisState:
    """Run news retrieval and analysis agent."""
    if not state.get("include_news", True):
        return {**state, "news_data": {"overall_sentiment": "neutral", "bullish_ratio": 0.5, "articles": []}}
    try:
        agent = NewsAgent()
        news_data = await agent.run(symbol=state["symbol"])
        steps = state.get("agent_steps", [])
        steps.append(f"News: sentiment={news_data['overall_sentiment']}, {news_data.get('total_count', 0)} articles")
        return {**state, "news_data": news_data, "agent_steps": steps}
    except Exception as e:
        logger.error("News node failed", error=str(e))
        return {**state, "news_data": {"overall_sentiment": "neutral", "bullish_ratio": 0.5, "articles": []}}


async def sentiment_node(state: InvestmentAnalysisState) -> InvestmentAnalysisState:
    """Run sentiment aggregation agent."""
    if not state.get("include_sentiment", True):
        return {**state, "sentiment_data": {"sentiment_score": 0.0, "sentiment_label": "neutral", "confidence": 0.5}}
    try:
        agent = SentimentAgent()
        sentiment_data = await agent.run(
            symbol=state["symbol"],
            news_data=state.get("news_data", {}),
            financial_data=state.get("financial_data", {}),
        )
        steps = state.get("agent_steps", [])
        steps.append(f"Sentiment: {sentiment_data['sentiment_label']} ({sentiment_data['sentiment_score']:+.2f})")
        return {**state, "sentiment_data": sentiment_data, "agent_steps": steps}
    except Exception as e:
        logger.error("Sentiment node failed", error=str(e))
        return {**state, "sentiment_data": {"sentiment_score": 0.0, "sentiment_label": "neutral", "confidence": 0.5}}


async def risk_node(state: InvestmentAnalysisState) -> InvestmentAnalysisState:
    """Run risk assessment agent."""
    try:
        agent = RiskAgent()
        risk_data = await agent.run(
            symbol=state["symbol"],
            portfolio_context=state.get("portfolio_context"),
        )
        steps = state.get("agent_steps", [])
        steps.append(f"Risk: level={risk_data['risk_level']}, score={risk_data['risk_score']}/10")
        return {**state, "risk_data": risk_data, "agent_steps": steps}
    except Exception as e:
        logger.error("Risk node failed", error=str(e))
        return {**state, "risk_data": {"risk_level": "unknown", "risk_score": 5.0, "risk_factors": []}}


async def reasoning_node(state: InvestmentAnalysisState) -> InvestmentAnalysisState:
    """
    Aggregate all agent outputs into a coherent reasoning summary.
    This acts as a synthesis step before the final recommendation.
    """
    financial = state.get("financial_data", {})
    news = state.get("news_data", {})
    sentiment = state.get("sentiment_data", {})
    risk = state.get("risk_data", {})
    memory = state.get("memory_context", {})

    symbol = state["symbol"]
    price = financial.get("price_data", {}).get("current_price", "N/A")

    reasoning_parts = [
        f"=== Reasoning Summary for {symbol} ===",
        f"Current Price: {price}",
        f"Financial Signals: {', '.join(financial.get('signals', ['None detected']))}",
        f"News Sentiment: {news.get('overall_sentiment', 'unknown')} "
        f"({news.get('bullish_count', 0)} bullish / {news.get('bearish_count', 0)} bearish)",
        f"Market Sentiment Score: {sentiment.get('sentiment_score', 0):+.2f} "
        f"({sentiment.get('sentiment_label', 'neutral')})",
        f"Risk Assessment: {risk.get('risk_level', 'unknown')} "
        f"(score {risk.get('risk_score', 5)}/10)",
    ]

    if risk.get("risk_factors"):
        reasoning_parts.append(f"Risk Factors: {'; '.join(risk['risk_factors'])}")
    if memory.get("context_summary"):
        reasoning_parts.append(f"User Memory: {memory['context_summary'][:200]}")

    reasoning_summary = "\n".join(reasoning_parts)
    steps = state.get("agent_steps", [])
    steps.append("Reasoning: aggregated all agent outputs")

    return {**state, "reasoning_summary": reasoning_summary, "agent_steps": steps}


async def recommendation_node(state: InvestmentAnalysisState) -> InvestmentAnalysisState:
    """Generate final BUY/HOLD/SELL recommendation using StrategyAgent."""
    try:
        agent = StrategyAgent()
        recommendation = await agent.run(
            symbol=state["symbol"],
            financial_data=state.get("financial_data", {}),
            news_data=state.get("news_data", {}),
            sentiment_data=state.get("sentiment_data", {}),
            risk_data=state.get("risk_data", {}),
            user_risk_tolerance=state["user_risk_tolerance"],
        )
        steps = state.get("agent_steps", [])
        steps.append(
            f"Recommendation: {recommendation['action']} "
            f"(confidence {recommendation['confidence']:.0%})"
        )
        return {
            **state,
            "recommendation": recommendation,
            "agent_steps": steps,
            "completed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("Recommendation node failed", error=str(e))
        return {**state, "error": f"Recommendation error: {str(e)}"}


async def memory_store_node(state: InvestmentAnalysisState) -> InvestmentAnalysisState:
    """Persist the completed analysis to long-term memory."""
    try:
        if state.get("recommendation") and state.get("user_id"):
            agent = MemoryAgent()
            await agent.store_analysis(
                user_id=state["user_id"],
                symbol=state["symbol"],
                recommendation=state["recommendation"],
                sentiment_data=state.get("sentiment_data", {}),
            )
        steps = state.get("agent_steps", [])
        steps.append("Memory: analysis stored for future reference")
        return {**state, "agent_steps": steps}
    except Exception as e:
        logger.warning("Memory store failed, continuing", error=str(e))
        return state


# ─── Conditional Edges ────────────────────────────────────────────────────────

def should_continue_after_financial(state: InvestmentAnalysisState) -> str:
    """Skip news/sentiment if financial data completely failed."""
    if state.get("financial_data", {}).get("error") and not state.get("financial_data", {}).get("price_data"):
        return "skip_to_recommendation"
    return "continue"


def _state_keys() -> set[str]:
    """Return all graph state keys for node-name conflict validation."""
    return set(InvestmentAnalysisState.__annotations__)


def _validate_node_names(node_names: Iterable[str]) -> None:
    conflicts = sorted(set(node_names) & _state_keys())
    if conflicts:
        names = ", ".join(conflicts)
        raise ValueError(
            f"LangGraph node name(s) conflict with state key(s): {names}. "
            "Use unique node names that are not state fields."
        )


# ─── Graph Assembly ───────────────────────────────────────────────────────────

def build_investment_graph() -> StateGraph:
    """
    Assemble the full multi-agent investment analysis graph.

    Execution pattern:
    Nodes run sequentially to avoid multi-edge reducer requirements in the
    installed LangGraph version. This preserves the full analysis pipeline while
    keeping state updates deterministic.
    """
    graph = StateGraph(InvestmentAnalysisState)

    nodes = {
        "planner": planner_node,
        "memory_retrieval": memory_retrieval_node,
        "financial": financial_node,
        "news": news_node,
        "sentiment": sentiment_node,
        "risk": risk_node,
        "reasoning": reasoning_node,
        "recommendation_agent": recommendation_node,
        "memory_store": memory_store_node,
    }
    _validate_node_names(nodes)

    # Register all nodes
    for name, node in nodes.items():
        graph.add_node(name, node)

    # Entry point
    graph.set_entry_point("planner")

    # Linear flow
    graph.add_edge("planner", "memory_retrieval")
    graph.add_edge("memory_retrieval", "financial")
    graph.add_edge("financial", "news")
    graph.add_edge("news", "sentiment")
    graph.add_edge("risk", "reasoning")
    graph.add_edge("sentiment", "risk")

    # Final pipeline
    graph.add_edge("reasoning", "recommendation_agent")
    graph.add_edge("recommendation_agent", "memory_store")
    graph.add_edge("memory_store", END)

    return graph.compile()


# Module-level compiled graph (compiled once, reused per request)
_compiled_graph = None


def get_investment_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_investment_graph()
    return _compiled_graph
