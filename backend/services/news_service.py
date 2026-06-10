"""
services/news_service.py — NewsAPI integration with FinBERT sentiment.
"""

import asyncio
from datetime import datetime
from typing import Optional
import aiohttp

from config import settings
from core.logging import logger
from schemas.schemas import NewsResponse, NewsArticle
from services.sentiment_service import SentimentService


class NewsService:
    def __init__(self):
        self.api_key = settings.NEWS_API_KEY
        self.base_url = settings.NEWS_API_BASE_URL
        self._sentiment_service: Optional[SentimentService] = None

    def _get_sentiment(self) -> SentimentService:
        if self._sentiment_service is None:
            self._sentiment_service = SentimentService()
        return self._sentiment_service

    async def fetch_news(self, query: str, page_size: int = 20) -> list[dict]:
        """Fetch articles from NewsAPI."""
        if not self.api_key:
            logger.warning("NEWS_API_KEY not configured, returning mock news")
            return self._mock_news(query)

        params = {
            "q": query,
            "apiKey": self.api_key,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": min(page_size, 100),
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/everything",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        logger.error("NewsAPI error", status=resp.status)
                        return self._mock_news(query)
                    data = await resp.json()
                    return data.get("articles", [])
        except Exception as e:
            logger.error("NewsAPI fetch failed", error=str(e))
            return self._mock_news(query)

    async def get_analyzed_news(self, query: str, page_size: int = 20) -> NewsResponse:
        """Fetch + analyze sentiment for each article."""
        articles_raw = await self.fetch_news(query, page_size)
        sentiment_svc = self._get_sentiment()

        analyzed_articles = []
        bullish_count = bearish_count = neutral_count = 0

        for article in articles_raw[:page_size]:
            title = article.get("title", "")
            description = article.get("description", "")
            text_to_analyze = f"{title}. {description}"

            # Run FinBERT sentiment
            sentiment_result = await sentiment_svc.analyze_text(text_to_analyze)
            label = sentiment_result.get("label", "neutral")
            score = sentiment_result.get("score", 0.5)

            # Map FinBERT labels to our domain labels
            if label == "positive":
                domain_label = "bullish"
                bullish_count += 1
            elif label == "negative":
                domain_label = "bearish"
                bearish_count += 1
            else:
                domain_label = "neutral"
                neutral_count += 1

            published = None
            if article.get("publishedAt"):
                try:
                    published = datetime.fromisoformat(
                        article["publishedAt"].replace("Z", "+00:00")
                    )
                except Exception:
                    pass

            analyzed_articles.append(NewsArticle(
                title=title,
                description=description,
                url=article.get("url", ""),
                source=article.get("source", {}).get("name", "Unknown"),
                published_at=published,
                sentiment=domain_label,
                sentiment_score=round(score, 4),
                summary=description[:200] if description else None,
            ))

        total = len(analyzed_articles)
        if bullish_count > bearish_count and bullish_count > neutral_count:
            overall = "bullish"
        elif bearish_count > bullish_count and bearish_count > neutral_count:
            overall = "bearish"
        else:
            overall = "neutral"

        return NewsResponse(
            articles=analyzed_articles,
            total_count=total,
            bullish_count=bullish_count,
            bearish_count=bearish_count,
            neutral_count=neutral_count,
            overall_sentiment=overall,
            query=query,
        )

    def _mock_news(self, query: str) -> list[dict]:
        """Return mock news when API key is not configured."""
        return [
            {
                "title": f"Market Update: {query} shows strong momentum",
                "description": f"Analysts are bullish on {query} following strong quarterly results.",
                "url": "https://example.com/news/1",
                "source": {"name": "Financial Times"},
                "publishedAt": datetime.utcnow().isoformat() + "Z",
            },
            {
                "title": f"{query}: What investors need to know",
                "description": f"Key metrics and technical analysis for {query} suggest cautious optimism.",
                "url": "https://example.com/news/2",
                "source": {"name": "Bloomberg"},
                "publishedAt": datetime.utcnow().isoformat() + "Z",
            },
        ]
