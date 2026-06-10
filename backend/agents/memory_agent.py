"""
agents/memory_agent.py — Memory retrieval and persistence agent.

In the workflow, this agent:
1. Retrieves relevant user memories BEFORE analysis (inject context)
2. Stores the completed analysis AFTER (for future retrieval)
"""

from typing import Optional

from core.logging import logger
from memory.memory_manager import MemoryManager


class MemoryAgent:
    """Manages memory retrieval and storage within the multi-agent workflow."""

    async def retrieve_context(
        self, user_id: str, query: str
    ) -> dict:
        """Retrieve relevant user memories to inform the analysis."""
        logger.info("MemoryAgent retrieving context", user_id=user_id)
        manager = MemoryManager(user_id)
        context = await manager.get_user_context_summary(query)
        preferences = await manager.retrieve_relevant_memory(query, n_results=3, memory_type="preference")

        return {
            "context_summary": context,
            "user_preferences": [p["content"] for p in preferences],
            "agent": "memory",
        }

    async def store_analysis(
        self,
        user_id: str,
        symbol: str,
        recommendation: dict,
        sentiment_data: dict,
    ) -> None:
        """Store analysis result in long-term memory for future reference."""
        manager = MemoryManager(user_id)
        content = (
            f"Analysis of {symbol} on {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d')}: "
            f"Recommendation: {recommendation.get('action')}, "
            f"Confidence: {recommendation.get('confidence'):.0%}, "
            f"Sentiment: {sentiment_data.get('sentiment_label')}, "
            f"Reasoning: {recommendation.get('reasoning', '')[:200]}"
        )
        await manager.store_long_term(
            content=content,
            memory_type="analysis",
            metadata={"symbol": symbol, "action": recommendation.get("action")},
        )
        logger.info("MemoryAgent stored analysis", user_id=user_id, symbol=symbol)
