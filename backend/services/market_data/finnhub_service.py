"""Async Finnhub market-data client and service layer."""

from __future__ import annotations

import asyncio
import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
import numpy as np
import pandas as pd
import redis.asyncio as redis

from config import settings
from core.logging import logger
import yfinance as yf


class FinnhubClient:
    """Small async client wrapper for official Finnhub REST endpoints."""

    RETRY_STATUSES = {408, 429, 500, 502, 503, 504}

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.FINNHUB_API_KEY
        self.base_url = (base_url or settings.FINNHUB_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.FINNHUB_TIMEOUT_SECONDS
        self.max_retries = max_retries if max_retries is not None else settings.FINNHUB_MAX_RETRIES
        self._client = client
        self._owns_client = client is None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            timeout = httpx.Timeout(self.timeout, connect=min(self.timeout, 5.0))
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=timeout,
                headers={"Accept": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    async def get(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any] | list[Any]:
        if not self.api_key:
            logger.warning("Finnhub API key missing")
            return self._error("MISSING_API_KEY", "FINNHUB_API_KEY is not configured.")

        request_params = dict(params or {})
        request_params["token"] = self.api_key
        client = await self._get_client()

        for attempt in range(self.max_retries + 1):
            try:
                response = await client.get(endpoint, params=request_params)
                if response.status_code in self.RETRY_STATUSES and attempt < self.max_retries:
                    await self._backoff(attempt)
                    continue
                if response.status_code == 429:
                    logger.warning("Finnhub rate limit hit", endpoint=endpoint)
                    return self._error("RATE_LIMITED", "Finnhub rate limit exceeded.")
                if response.is_error:
                    logger.error(
                        f"""
                           FINNHUB ERROR
                            Endpoint: {endpoint}
                            Status: {response.status_code}
                            Params: {request_params}
                            Response: {response.text}
                        """
                    )
                    return self._error(
                        "FINNHUB_HTTP_ERROR",
                        f"Finnhub returned HTTP {response.status_code}.",
                    )
                return response.json()
            except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as exc:
                if attempt < self.max_retries:
                    logger.warning("Finnhub request retrying", endpoint=endpoint, error=str(exc), attempt=attempt + 1)
                    await self._backoff(attempt)
                    continue
                logger.warning("Finnhub request failed after retries", endpoint=endpoint, error=str(exc))
                return self._error("FINNHUB_TIMEOUT", "Finnhub request timed out.")
            except Exception as exc:
                logger.exception("Unexpected Finnhub client error", endpoint=endpoint)
                return self._error("FINNHUB_CLIENT_ERROR", str(exc))

        return self._error("FINNHUB_REQUEST_FAILED", "Finnhub request failed.")

    async def _backoff(self, attempt: int) -> None:
        await asyncio.sleep(min(2**attempt * 0.5, 4.0))

    @staticmethod
    def _error(code: str, message: str) -> dict[str, Any]:
        return {"error": {"code": code, "message": message}}


class RedisCache:
    """Best-effort Redis cache; silently bypasses when Redis is unavailable."""

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
        self._enabled = True

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=0.2,
                socket_timeout=0.2,
            )
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        if not self._enabled:
            return None
        try:
            client = await self._get_client()
            raw = await client.get(key)
            return json.loads(raw) if raw else None
        except Exception as exc:
            self._enabled = False
            logger.debug("Redis cache get skipped", key=key, error=str(exc))
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        if not self._enabled:
            return
        try:
            client = await self._get_client()
            await client.setex(key, ttl_seconds, json.dumps(value, default=str))
        except Exception as exc:
            self._enabled = False
            logger.debug("Redis cache set skipped", key=key, error=str(exc))

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


class FinnhubService:
    """Market-data service with caching and response normalization."""

    def __init__(self, client: Optional[FinnhubClient] = None, cache: Optional[RedisCache] = None) -> None:
        self.client = client or FinnhubClient()
        self.cache = cache if cache is not None else RedisCache(settings.REDIS_URL)

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        symbol = self._normalize_symbol(symbol)
        cache_key = f"market:quote:{symbol}"
        cached = await self.cache.get(cache_key) if self.cache else None
        if cached:
            return cached

        quote = await self.client.get("/quote", {"symbol": symbol})
        if self._has_error(quote):
            return quote
        if not quote or not quote.get("c"):
            return self._error("SYMBOL_NOT_FOUND", f"No quote data found for {symbol}.")

        profile = await self.get_company_profile(symbol)
        change = self._to_float(quote.get("d"))
        previous_close = self._to_float(quote.get("pc"))
        change_pct = self._to_float(quote.get("dp"))
        result = {
            "symbol": symbol,
            "current_price": self._round(quote.get("c")),
            "previous_close": self._round(previous_close),
            "change": self._round(change),
            "change_pct": self._round(change_pct),
            "volume": self._to_int(quote.get("v")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "exchange": profile.get("exchange") if isinstance(profile, dict) else None,
            "country": profile.get("country") if isinstance(profile, dict) else None,
            "currency": profile.get("currency") if isinstance(profile, dict) else None,
            "company_name": profile.get("name") if isinstance(profile, dict) else None,
            "market_cap": profile.get("marketCapitalization") if isinstance(profile, dict) else None,
        }
        await self.cache.set(cache_key, result, 60) if self.cache else None
        return result

    async def get_company_profile(self, symbol: str) -> dict[str, Any]:
        symbol = self._normalize_symbol(symbol)
        cache_key = f"market:profile:{symbol}"
        cached = await self.cache.get(cache_key) if self.cache else None
        if cached:
            return cached

        profile = await self.client.get("/stock/profile2", {"symbol": symbol})
        if self._has_error(profile):
            return profile
        if not profile:
            return self._error("SYMBOL_NOT_FOUND", f"No company profile found for {symbol}.")
        profile["symbol"] = profile.get("ticker") or symbol
        await self.cache.set(cache_key, profile, 24 * 60 * 60) if self.cache else None
        return profile

    async def get_stock_news(self, symbol: str) -> dict[str, Any]:
        symbol = self._normalize_symbol(symbol)
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=7)
        news = await self.client.get("/company-news", {"symbol": symbol, "from": start.isoformat(), "to": today.isoformat()})
        if self._has_error(news):
            return news
        return {"symbol": symbol, "articles": news or [], "count": len(news or [])}

    async def get_recommendations(self, symbol: str) -> dict[str, Any]:
        symbol = self._normalize_symbol(symbol)
        data = await self.client.get("/stock/recommendation", {"symbol": symbol})
        if self._has_error(data):
            return data
        return {"symbol": symbol, "recommendations": data or []}

    async def get_basic_financials(self, symbol: str) -> dict[str, Any]:
        symbol = self._normalize_symbol(symbol)
        data = await self.client.get("/stock/metric", {"symbol": symbol, "metric": "all"})
        if self._has_error(data):
            return data
        if not data:
            return self._error("SYMBOL_NOT_FOUND", f"No basic financials found for {symbol}.")
        data["symbol"] = data.get("symbol") or symbol
        return data

    async def get_historical_candles(self, symbol: str, period: str = "1y") -> dict[str, Any]:
        symbol = self._normalize_symbol(symbol)
        cache_key = f"market:history:{symbol}:{period}"
        cached = await self.cache.get(cache_key) if self.cache else None
        if cached:
            return cached

        try:
            history = await asyncio.to_thread(self._download_yfinance_history, symbol, period)
        except Exception as exc:
            logger.warning("Yahoo Finance historical fetch failed", symbol=symbol, period=period, error=str(exc))
            return self._error("YAHOO_HISTORY_ERROR", "Yahoo Finance historical data request failed.")

        if history.empty:
            return self._error("NO_HISTORICAL_DATA", f"No historical candle data found for {symbol}.")

        if isinstance(history.columns, pd.MultiIndex):
            history.columns = history.columns.get_level_values(0)
        history = history.dropna(subset=["Open", "High", "Low", "Close"])
        if history.empty:
            return self._error("NO_HISTORICAL_DATA", f"No usable historical candle data found for {symbol}.")

        payload = {
            "symbol": symbol,
            "period": period,
            "s": "ok",
            "c": [self._to_float(v) for v in history["Close"].tolist()],
            "o": [self._to_float(v) for v in history["Open"].tolist()],
            "h": [self._to_float(v) for v in history["High"].tolist()],
            "l": [self._to_float(v) for v in history["Low"].tolist()],
            "v": [self._to_int(v) or 0 for v in history.get("Volume", pd.Series([0] * len(history))).tolist()],
            "t": [int(ts.timestamp()) for ts in history.index.to_pydatetime()],
        }
        await self.cache.set(cache_key, payload, 5 * 60) if self.cache else None
        return payload

    async def get_technical_indicators(self, symbol: str, period: str = "1y") -> dict[str, Any]:
        symbol = self._normalize_symbol(symbol)
        cache_key = f"market:technical:{symbol}:{period}"
        cached = await self.cache.get(cache_key) if self.cache else None
        if cached:
            return cached

        candles = await self.get_historical_candles(symbol, period)
        if self._has_error(candles):
            return candles
        df = self._candles_to_frame(candles)
        if len(df) < 50:
            return self._error("INSUFFICIENT_DATA", "Insufficient data for technical analysis.")

        close = df["close"]
        sma_20 = close.rolling(window=20).mean()
        sma_50 = close.rolling(window=50).mean()
        sma_200 = close.rolling(window=200).mean()
        rsi = self._rsi(close)
        macd, signal_line = self._macd(close)
        returns = close.pct_change().dropna()

        current_price = self._round(close.iloc[-1])
        result = {
            "symbol": symbol,
            "period": period,
            "current_price": current_price,
            "sma_20": self._round(sma_20.iloc[-1]),
            "sma_50": self._round(sma_50.iloc[-1]),
            "sma_200": self._round(sma_200.iloc[-1]),
            "rsi": self._round(rsi.iloc[-1], 2),
            "macd": self._round(macd.iloc[-1]),
            "signal_line": self._round(signal_line.iloc[-1]),
            "macd_signal": self._round(signal_line.iloc[-1]),
            "data_points": len(df),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signals": self._technical_signals(current_price, sma_20.iloc[-1], sma_50.iloc[-1], rsi.iloc[-1], macd.iloc[-1], signal_line.iloc[-1]),
        }
        if len(returns) > 1:
            result["volatility_annual"] = self._round(float(returns.std()) * math.sqrt(252))
            result["avg_daily_return"] = self._round(float(returns.mean()), 6)
        await self.cache.set(cache_key, result, 5 * 60) if self.cache else None
        return result

    async def get_volatility(self, symbol: str, period: str = "1y") -> dict[str, Any]:
        symbol = self._normalize_symbol(symbol)
        candles = await self.get_historical_candles(symbol, period)
        if self._has_error(candles):
            return candles
        df = self._candles_to_frame(candles)
        if len(df) < 30:
            return self._error("INSUFFICIENT_DATA", "Insufficient data for volatility calculation.")
        returns = df["close"].pct_change().dropna()
        cumulative = (1 + returns).cumprod()
        drawdown = (cumulative - cumulative.expanding().max()) / cumulative.expanding().max()
        std = float(returns.std())
        return {
            "symbol": symbol,
            "volatility_annual": self._round(std * math.sqrt(252)),
            "volatility_30d": self._round(float(returns.tail(30).std()) * math.sqrt(252)),
            "max_drawdown": self._round(float(drawdown.min())),
            "beta": None,
            "avg_daily_return": self._round(float(returns.mean()), 6),
            "sharpe_ratio": self._round(float(returns.mean()) / std * math.sqrt(252), 3) if std > 0 else None,
        }

    async def get_historical_summary(self, symbol: str, period: str = "1y") -> dict[str, Any]:
        symbol = self._normalize_symbol(symbol)
        candles = await self.get_historical_candles(symbol, period)
        if self._has_error(candles):
            return candles
        df = self._candles_to_frame(candles)
        return {
            "symbol": symbol,
            "period": period,
            "data_points": len(df),
            "start_date": df.index[0].isoformat(),
            "end_date": df.index[-1].isoformat(),
            "latest_close": self._round(df["close"].iloc[-1]),
            "highest": self._round(df["high"].max()),
            "lowest": self._round(df["low"].min()),
            "avg_volume": self._round(df["volume"].mean(), 0),
            "price_change_pct": self._round((df["close"].iloc[-1] - df["close"].iloc[0]) / df["close"].iloc[0] * 100),
        }

    @staticmethod
    def _candles_to_frame(candles: dict[str, Any]) -> pd.DataFrame:
        df = pd.DataFrame(
            {
                "open": candles["o"],
                "high": candles["h"],
                "low": candles["l"],
                "close": candles["c"],
                "volume": candles.get("v", [None] * len(candles["c"])),
            },
            index=pd.to_datetime(candles["t"], unit="s", utc=True),
        )
        return df.sort_index()

    @staticmethod
    def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(window=period, min_periods=period).mean()
        loss = (-delta.clip(upper=0)).rolling(window=period, min_periods=period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.mask((loss == 0) & (gain > 0), 100)
        rsi = rsi.mask((loss == 0) & (gain == 0), 50)
        return rsi

    @staticmethod
    def _macd(close: pd.Series) -> tuple[pd.Series, pd.Series]:
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd, signal

    @staticmethod
    def _technical_signals(current: Optional[float], sma_20: float, sma_50: float, rsi: float, macd: float, signal: float) -> list[str]:
        signals: list[str] = []
        if pd.notna(rsi):
            if rsi > 70:
                signals.append("RSI overbought (>70)")
            elif rsi < 30:
                signals.append("RSI oversold (<30)")
            else:
                signals.append(f"RSI neutral ({rsi:.1f})")
        if pd.notna(macd) and pd.notna(signal):
            signals.append("MACD bullish crossover" if macd > signal else "MACD bearish crossover")
        if current is not None and pd.notna(sma_20) and pd.notna(sma_50):
            if current > sma_20 > sma_50:
                signals.append("Price above SMA20>SMA50 (uptrend)")
            elif current < sma_20 < sma_50:
                signals.append("Price below SMA20<SMA50 (downtrend)")
        return signals

    @staticmethod
    def _period_to_timedelta(period: str) -> timedelta:
        period = (period or "1y").lower()
        mapping = {
            "1mo": timedelta(days=31),
            "3mo": timedelta(days=93),
            "6mo": timedelta(days=186),
            "1y": timedelta(days=370),
            "2y": timedelta(days=740),
            "5y": timedelta(days=1850),
        }
        return mapping.get(period, timedelta(days=370))

    @staticmethod
    def _download_yfinance_history(symbol: str, period: str) -> pd.DataFrame:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period or "1y", interval="1d", auto_adjust=False)
        if not history.empty:
            return history
        return yf.download(
            symbol,
            period=period or "1y",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        return symbol.strip().upper()

    @staticmethod
    def _has_error(payload: Any) -> bool:
        return isinstance(payload, dict) and "error" in payload

    @staticmethod
    def _error(code: str, message: str) -> dict[str, Any]:
        return {"error": {"code": code, "message": message}}

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        try:
            if value is None or pd.isna(value):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        try:
            if value is None or pd.isna(value):
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _round(cls, value: Any, digits: int = 4) -> Optional[float]:
        numeric = cls._to_float(value)
        if numeric is None or not math.isfinite(numeric):
            return None
        return round(numeric, digits)
