"""
agents/strategy_agent.py — Strategy and recommendation generation agent.

Takes aggregated data from all agents and produces:
- BUY / HOLD / SELL recommendation
- Confidence score (0–1)
- Price targets
- Risk-adjusted reasoning

Uses OpenAI GPT-4o for explainable natural-language reasoning.
If LLM is unavailable, falls back to rule-based scoring.
"""

import asyncio
from datetime import datetime
from typing import Optional

from config import settings
from core.logging import logger


RECOMMENDATION_SYSTEM_PROMPT = """You are a professional investment analyst AI. 
You will receive structured data from multiple analysis agents and must produce 
a clear, well-reasoned investment recommendation.

Your output must be a JSON object with exactly these fields:
{
  "action": "BUY" | "HOLD" | "SELL",
  "confidence": 0.0–1.0,
  "reasoning": "2–4 sentence explanation citing specific data points",
  "risk_level": "low" | "medium" | "high" | "very_high",
  "time_horizon": "short" | "medium" | "long",
  "price_target_bull": null or number,
  "price_target_bear": null or number,
  "risk_factors": ["list", "of", "risk", "strings"],
  "supporting_factors": ["list", "of", "supporting", "strings"]
}

Base your recommendation on:
- Technical indicators (RSI, MACD, SMA crossovers)
- News sentiment (bullish/bearish ratio)
- Risk metrics (volatility, beta, max drawdown)
- Market sentiment composite score
- User's risk tolerance

Be conservative: if data is mixed or unclear, recommend HOLD.
Never recommend against the user's stated risk tolerance."""


class StrategyAgent:
    """Generates final investment recommendation using LLM reasoning."""

    def _get_llm(self):
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.1,
                api_key=settings.OPENAI_API_KEY,
            )
        except Exception:
            return None

    async def run(
        self,
        symbol: str,
        financial_data: dict,
        news_data: dict,
        sentiment_data: dict,
        risk_data: dict,
        user_risk_tolerance: str = "moderate",
    ) -> dict:
        logger.info("StrategyAgent running", symbol=symbol)

        # Try LLM-based reasoning first
        llm_result = await self._llm_recommendation(
            symbol, financial_data, news_data, sentiment_data, risk_data, user_risk_tolerance
        )
        if llm_result:
            llm_result["agent"] = "strategy"
            llm_result["symbol"] = symbol
            return llm_result

        # Fallback: rule-based recommendation
        return self._rule_based_recommendation(
            symbol, financial_data, news_data, sentiment_data, risk_data, user_risk_tolerance
        )

    async def _llm_recommendation(
        self,
        symbol: str,
        financial_data: dict,
        news_data: dict,
        sentiment_data: dict,
        risk_data: dict,
        user_risk_tolerance: str,
    ) -> Optional[dict]:
        llm = self._get_llm()
        if not llm or not settings.OPENAI_API_KEY:
            return None

        # Build a concise data summary for the LLM
        price_data = financial_data.get("price_data", {})
        tech_data = financial_data.get("technical_data", {})

        data_summary = f"""
SYMBOL: {symbol}
USER RISK TOLERANCE: {user_risk_tolerance}

=== PRICE DATA ===
Current Price: {price_data.get('current_price')}
24h Change: {price_data.get('change_pct')}%
Market Cap: {price_data.get('market_cap')}
Company: {price_data.get('company_name')}

=== TECHNICAL INDICATORS ===
RSI (14): {tech_data.get('rsi')}
MACD: {tech_data.get('macd')} | Signal: {tech_data.get('macd_signal')}
SMA 20: {tech_data.get('sma_20')} | SMA 50: {tech_data.get('sma_50')}
Bollinger Upper: {tech_data.get('bollinger_upper')} | Lower: {tech_data.get('bollinger_lower')}
Technical Signals: {', '.join(tech_data.get('signals', []))}

=== NEWS SENTIMENT ===
Overall: {news_data.get('overall_sentiment')}
Bullish/Bearish/Neutral: {news_data.get('bullish_count')}/{news_data.get('bearish_count')}/{news_data.get('neutral_count')}
Summary: {news_data.get('news_summary', '')[:400]}

=== MARKET SENTIMENT ===
Composite Score: {sentiment_data.get('sentiment_score')} (-1.0 bear → +1.0 bull)
Label: {sentiment_data.get('sentiment_label')}
Confidence: {sentiment_data.get('confidence')}

=== RISK METRICS ===
Risk Level: {risk_data.get('risk_level')}
Risk Score: {risk_data.get('risk_score')}/10
Annual Volatility: {risk_data.get('volatility_annual')}
Beta: {risk_data.get('beta')}
Max Drawdown: {risk_data.get('max_drawdown')}
Sharpe Ratio: {risk_data.get('sharpe_ratio')}
Risk Factors: {', '.join(risk_data.get('risk_factors', []))}
"""

        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: llm.invoke([
                    SystemMessage(content=RECOMMENDATION_SYSTEM_PROMPT),
                    HumanMessage(content=f"Analyze this data and provide your recommendation:\n{data_summary}"),
                ])
            )

            import json
            content = response.content if hasattr(response, "content") else str(response)
            # Strip markdown fences if present
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            result = json.loads(content.strip())

            # Normalize fields
            return {
                "action": result.get("action", "HOLD").upper(),
                "confidence": float(result.get("confidence", 0.5)),
                "reasoning": result.get("reasoning", ""),
                "risk_level": result.get("risk_level", "medium"),
                "time_horizon": result.get("time_horizon", "medium"),
                "price_targets": {
                    "bull": result.get("price_target_bull"),
                    "bear": result.get("price_target_bear"),
                },
                "risk_factors": result.get("risk_factors", []),
                "supporting_factors": result.get("supporting_factors", []),
                "method": "llm",
            }
        except Exception as e:
            logger.warning("LLM strategy generation failed, using rules", error=str(e))
            return None

    def _rule_based_recommendation(
        self,
        symbol: str,
        financial_data: dict,
        news_data: dict,
        sentiment_data: dict,
        risk_data: dict,
        user_risk_tolerance: str,
    ) -> dict:
        """Deterministic fallback when LLM is unavailable."""
        score = 0.0  # Negative = sell, positive = buy

        # Sentiment contribution (-3 to +3)
        sentiment_score = sentiment_data.get("sentiment_score", 0)
        score += sentiment_score * 3.0

        # News contribution (-2 to +2)
        bullish_ratio = news_data.get("bullish_ratio", 0.5)
        score += (bullish_ratio - 0.5) * 4.0

        # Technical contribution (-2 to +2)
        tech = financial_data.get("technical_data", {})
        rsi = tech.get("rsi", 50)
        if rsi < 30: score += 1.5
        elif rsi > 70: score -= 1.5
        macd = tech.get("macd", 0)
        macd_sig = tech.get("macd_signal", 0)
        if macd and macd_sig:
            score += 1.0 if macd > macd_sig else -1.0

        # Risk penalty
        risk_level = risk_data.get("risk_level", "medium")
        risk_multiplier = {
            "low": 1.0, "medium": 0.8, "high": 0.6, "very_high": 0.4,
            "conservative": 0.5, "moderate": 0.7, "aggressive": 0.9,
        }
        tolerance_multiplier = risk_multiplier.get(user_risk_tolerance, 0.7)

        # Adjust for risk tolerance
        if user_risk_tolerance == "conservative" and risk_level in ("high", "very_high"):
            score *= 0.4  # Dampen bullish signals for conservative users

        if score > 1.5:
            action = "BUY"
            confidence = min(0.9, 0.5 + score / 10)
        elif score < -1.5:
            action = "SELL"
            confidence = min(0.9, 0.5 + abs(score) / 10)
        else:
            action = "HOLD"
            confidence = 0.5

        confidence *= tolerance_multiplier

        return {
            "symbol": symbol,
            "action": action,
            "confidence": round(confidence, 4),
            "reasoning": (
                f"Rule-based analysis of {symbol}: Sentiment score {sentiment_score:.2f}, "
                f"news bullish ratio {bullish_ratio:.0%}, RSI {rsi:.1f}. "
                f"Risk level is {risk_level}. "
                f"Based on these factors, {action} is recommended for {user_risk_tolerance} risk tolerance."
            ),
            "risk_level": risk_level,
            "time_horizon": "medium",
            "price_targets": {"bull": None, "bear": None},
            "risk_factors": risk_data.get("risk_factors", []),
            "supporting_factors": financial_data.get("signals", []),
            "method": "rule_based",
            "agent": "strategy",
        }
