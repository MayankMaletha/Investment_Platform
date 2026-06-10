"""
agents/news_agent.py — News retrieval and summarization agent.

Fetches, analyzes, and summarizes financial news for a given symbol.
Outputs a news_data dict for the LangGraph state.
"""

from core.logging import logger
from services.news_service import NewsService


class NewsAgent:
    """Fetches and analyzes financial news for a given asset."""

    def __init__(self):
        self.news_service = NewsService()

    async def run(self, symbol: str, page_size: int = 10) -> dict:
        logger.info("NewsAgent running", symbol=symbol)

        news_response = await self.news_service.get_analyzed_news(
            query=symbol, page_size=page_size
        )

        # Build a plain-text summary for the reasoning node
        headlines = [a.title for a in news_response.articles[:5]]
        bullish_ratio = (
            news_response.bullish_count / news_response.total_count
            if news_response.total_count > 0 else 0.5
        )

        summary_lines = [f"Overall news sentiment: {news_response.overall_sentiment}"]
        summary_lines.append(
            f"Out of {news_response.total_count} articles: "
            f"{news_response.bullish_count} bullish, "
            f"{news_response.bearish_count} bearish, "
            f"{news_response.neutral_count} neutral."
        )
        if headlines:
            summary_lines.append("Top headlines:")
            summary_lines.extend(f"  - {h}" for h in headlines)

        result = {
            "symbol": symbol,
            "news_summary": "\n".join(summary_lines),
            "overall_sentiment": news_response.overall_sentiment,
            "bullish_count": news_response.bullish_count,
            "bearish_count": news_response.bearish_count,
            "neutral_count": news_response.neutral_count,
            "bullish_ratio": round(bullish_ratio, 3),
            "articles": [
                {
                    "title": a.title,
                    "sentiment": a.sentiment,
                    "sentiment_score": a.sentiment_score,
                    "source": a.source,
                }
                for a in news_response.articles[:10]
            ],
            "agent": "news",
        }
        logger.info("NewsAgent complete", symbol=symbol, sentiment=news_response.overall_sentiment)
        return result
