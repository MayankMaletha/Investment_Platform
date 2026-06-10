"""
services/sentiment_service.py — FinBERT sentiment analysis engine.

FinBERT is a BERT model fine-tuned on financial text by Prosus AI.
It outputs: positive / negative / neutral with a confidence score.

Design:
- Model loaded once at first use (lazy init) — avoids blocking startup
- Runs in a thread executor to keep FastAPI's event loop free
- Falls back gracefully if torch/transformers not available
"""

import asyncio
from typing import Optional
from functools import lru_cache

from core.logging import logger
from config import settings


class SentimentService:
    """Wraps FinBERT for async-safe financial sentiment analysis."""

    _pipeline = None  # Class-level singleton — shared across instances

    @classmethod
    def _load_pipeline(cls):
        """Load FinBERT pipeline once, lazily."""
        if cls._pipeline is not None:
            return cls._pipeline
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
            logger.info("Loading FinBERT model", model=settings.FINBERT_MODEL)
            tokenizer = AutoTokenizer.from_pretrained(settings.FINBERT_MODEL)
            model = AutoModelForSequenceClassification.from_pretrained(settings.FINBERT_MODEL)
            cls._pipeline = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                return_all_scores=True,
                truncation=True,
                max_length=512,
            )
            logger.info("FinBERT model loaded successfully")
            return cls._pipeline
        except Exception as e:
            logger.warning("FinBERT load failed, using fallback", error=str(e))
            return None

    async def analyze_text(self, text: str) -> dict:
        """
        Analyze a single text string.
        Returns: {"label": "positive"|"negative"|"neutral", "score": float, "all_scores": {...}}
        """
        if not text or not text.strip():
            return {"label": "neutral", "score": 0.5, "all_scores": {}}

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run_finbert, text[:512])

    def _run_finbert(self, text: str) -> dict:
        pipe = self._load_pipeline()
        if pipe is None:
            return self._heuristic_sentiment(text)

        try:
            results = pipe(text)
            # results is list of lists: [[{label, score}, ...]]
            scores_list = results[0] if isinstance(results[0], list) else results
            scores = {item["label"].lower(): item["score"] for item in scores_list}

            best_label = max(scores, key=scores.get)
            best_score = scores[best_label]

            return {
                "label": best_label,
                "score": round(best_score, 4),
                "all_scores": {k: round(v, 4) for k, v in scores.items()},
            }
        except Exception as e:
            logger.error("FinBERT inference failed", error=str(e))
            return self._heuristic_sentiment(text)

    def _heuristic_sentiment(self, text: str) -> dict:
        """
        Rule-based fallback when FinBERT is unavailable.
        Counts bullish/bearish keywords for a rough score.
        """
        text_lower = text.lower()
        bullish_words = [
            "buy", "bull", "surge", "rally", "gain", "profit", "growth",
            "strong", "beat", "exceed", "record", "rise", "up", "positive",
            "optimistic", "upgrade", "outperform", "momentum", "breakout",
        ]
        bearish_words = [
            "sell", "bear", "drop", "fall", "loss", "decline", "weak",
            "miss", "below", "down", "negative", "pessimistic", "downgrade",
            "underperform", "crash", "recession", "risk", "concern", "fear",
        ]
        bullish_count = sum(1 for w in bullish_words if w in text_lower)
        bearish_count = sum(1 for w in bearish_words if w in text_lower)

        total = bullish_count + bearish_count
        if total == 0:
            return {"label": "neutral", "score": 0.5, "all_scores": {"neutral": 0.5}}

        if bullish_count > bearish_count:
            score = min(0.5 + (bullish_count - bearish_count) / total * 0.5, 0.99)
            return {"label": "positive", "score": round(score, 4),
                    "all_scores": {"positive": round(score, 4), "negative": 0.1, "neutral": round(1 - score - 0.1, 4)}}
        elif bearish_count > bullish_count:
            score = min(0.5 + (bearish_count - bullish_count) / total * 0.5, 0.99)
            return {"label": "negative", "score": round(score, 4),
                    "all_scores": {"negative": round(score, 4), "positive": 0.1, "neutral": round(1 - score - 0.1, 4)}}
        else:
            return {"label": "neutral", "score": 0.5, "all_scores": {"neutral": 0.5, "positive": 0.25, "negative": 0.25}}

    async def analyze_batch(self, texts: list[str]) -> list[dict]:
        """Analyze multiple texts concurrently."""
        tasks = [self.analyze_text(t) for t in texts]
        return await asyncio.gather(*tasks)

    async def compute_market_emotion_score(self, texts: list[str]) -> dict:
        """
        Aggregate multiple text sentiments into a single market emotion score.
        Returns a score from -1.0 (extreme fear) to +1.0 (extreme greed).
        """
        if not texts:
            return {"score": 0.0, "label": "neutral", "confidence": 0.0}

        results = await self.analyze_batch(texts)

        total_score = 0.0
        for r in results:
            label = r.get("label", "neutral")
            score = r.get("score", 0.5)
            if label == "positive":
                total_score += score
            elif label == "negative":
                total_score -= score

        avg_score = total_score / len(results)
        avg_score = max(-1.0, min(1.0, avg_score))

        if avg_score > 0.3:
            label = "bullish"
        elif avg_score < -0.3:
            label = "bearish"
        else:
            label = "neutral"

        confidence = abs(avg_score)
        return {
            "score": round(avg_score, 4),
            "label": label,
            "confidence": round(confidence, 4),
            "analyzed_count": len(results),
        }
