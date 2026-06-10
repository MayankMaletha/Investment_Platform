"""
agents/sentiment_agent.py — Market sentiment aggregation agent.

Aggregates sentiment from:
1. News articles (FinBERT scored)
2. Technical indicator signals (RSI, MACD patterns)
3. Price action signals (trend, momentum)

Outputs a unified sentiment score and label for the reasoning node.
"""

from core.logging import logger
from services.sentiment_service import SentimentService


class SentimentAgent:
    """Computes a composite market sentiment score from multiple signals."""

    def __init__(self):
        self.sentiment_service = SentimentService()

    async def run(
        self,
        symbol: str,
        news_data: dict,
        financial_data: dict,
    ) -> dict:
        logger.info("SentimentAgent running", symbol=symbol)

        scores = []
        weight_sum = 0.0
        explanations = []

        # ── News Sentiment (weight: 0.35) ────────────────────────────────────
        news_sentiment = news_data.get("overall_sentiment", "neutral")
        bullish_ratio = news_data.get("bullish_ratio", 0.5)

        if news_sentiment == "bullish":
            news_score = bullish_ratio  # 0–1
        elif news_sentiment == "bearish":
            news_score = -(1.0 - bullish_ratio)
        else:
            news_score = 0.0

        scores.append(news_score * 0.35)
        weight_sum += 0.35
        explanations.append(f"News: {news_sentiment} (bullish ratio: {bullish_ratio:.0%})")

        # ── Technical Sentiment (weight: 0.40) ───────────────────────────────
        tech_data = financial_data.get("technical_data", {})
        tech_score = 0.0
        tech_count = 0

        rsi = tech_data.get("rsi")
        if rsi is not None:
            if rsi < 30:
                tech_score += 0.8   # Oversold → potential reversal up
                explanations.append(f"RSI oversold ({rsi:.1f}) — potential reversal")
            elif rsi > 70:
                tech_score -= 0.8   # Overbought → potential reversal down
                explanations.append(f"RSI overbought ({rsi:.1f}) — caution")
            else:
                tech_score += (rsi - 50) / 50 * 0.5  # Scaled [-0.5, 0.5]
            tech_count += 1

        macd = tech_data.get("macd")
        macd_signal = tech_data.get("macd_signal")
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                tech_score += 0.6
                explanations.append("MACD bullish crossover")
            else:
                tech_score -= 0.6
                explanations.append("MACD bearish crossover")
            tech_count += 1

        sma_20 = tech_data.get("sma_20")
        sma_50 = tech_data.get("sma_50")
        current_price = tech_data.get("current_price")
        if sma_20 and sma_50 and current_price:
            if current_price > sma_20 > sma_50:
                tech_score += 0.5
                explanations.append("Uptrend: price above SMA20 > SMA50")
            elif current_price < sma_20 < sma_50:
                tech_score -= 0.5
                explanations.append("Downtrend: price below SMA20 < SMA50")
            tech_count += 1

        if tech_count > 0:
            tech_score = max(-1.0, min(1.0, tech_score / tech_count))
            scores.append(tech_score * 0.40)
            weight_sum += 0.40

        # ── Volatility Sentiment (weight: 0.25) ──────────────────────────────
        vol_data = financial_data.get("volatility_data", {})
        vol = vol_data.get("volatility_annual", 0.2)
        # High volatility → lower sentiment (uncertainty penalty)
        vol_score = max(-0.5, 0.5 - vol)
        scores.append(vol_score * 0.25)
        weight_sum += 0.25
        explanations.append(f"Volatility: {vol:.0%} annual")

        # ── Composite Score ───────────────────────────────────────────────────
        composite = sum(scores) / weight_sum if weight_sum > 0 else 0.0
        composite = max(-1.0, min(1.0, composite))

        if composite > 0.25:
            label = "bullish"
            confidence = composite
        elif composite < -0.25:
            label = "bearish"
            confidence = abs(composite)
        else:
            label = "neutral"
            confidence = 1.0 - abs(composite) * 2

        result = {
            "symbol": symbol,
            "sentiment_score": round(composite, 4),
            "sentiment_label": label,
            "confidence": round(confidence, 4),
            "explanations": explanations,
            "news_component": round(news_score, 4),
            "technical_component": round(tech_score, 4),
            "volatility_component": round(vol_score, 4),
            "agent": "sentiment",
        }
        logger.info("SentimentAgent complete", symbol=symbol, label=label, score=composite)
        return result
