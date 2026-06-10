"""Tests for Finnhub market-data migration."""

from __future__ import annotations

import httpx
import pandas as pd
import pytest

from services.market_data.finnhub_service import FinnhubClient, FinnhubService


class NoopCache:
    async def get(self, key):
        return None

    async def set(self, key, value, ttl_seconds):
        return None


class FakeFinnhubClient:
    def __init__(self, responses):
        self.responses = responses

    async def get(self, endpoint, params=None):
        symbol = (params or {}).get("symbol")
        return self.responses.get((endpoint, symbol), self.responses.get(endpoint, {}))


def candle_payload(days: int = 230):
    closes = [100 + i * 0.5 for i in range(days)]
    return {
        "s": "ok",
        "t": [1_700_000_000 + i * 86_400 for i in range(days)],
        "o": [c - 0.5 for c in closes],
        "h": [c + 1.0 for c in closes],
        "l": [c - 1.0 for c in closes],
        "c": closes,
        "v": [1_000_000 + i for i in range(days)],
    }


def history_frame(days: int = 230):
    closes = [100 + i * 0.5 for i in range(days)]
    dates = pd.date_range("2025-01-01", periods=days, freq="D", tz="UTC")
    return pd.DataFrame(
        {
            "Open": [c - 0.5 for c in closes],
            "High": [c + 1.0 for c in closes],
            "Low": [c - 1.0 for c in closes],
            "Close": closes,
            "Volume": [1_000_000 + i for i in range(days)],
        },
        index=dates,
    )


@pytest.mark.asyncio
async def test_get_quote_us_stock():
    service = FinnhubService(
        client=FakeFinnhubClient({
            ("/quote", "AAPL"): {"c": 212.34, "pc": 210.11, "d": 2.23, "dp": 1.0613, "v": 12_000_000},
            ("/stock/profile2", "AAPL"): {
                "ticker": "AAPL",
                "name": "Apple Inc",
                "exchange": "NASDAQ NMS - GLOBAL MARKET",
                "country": "US",
                "currency": "USD",
            },
        }),
        cache=NoopCache(),
    )

    result = await service.get_quote("aapl")

    assert result["symbol"] == "AAPL"
    assert result["current_price"] == 212.34
    assert result["previous_close"] == 210.11
    assert result["change"] == 2.23
    assert result["change_pct"] == 1.0613
    assert result["volume"] == 12_000_000
    assert result["country"] == "US"
    assert result["currency"] == "USD"


@pytest.mark.asyncio
async def test_get_quote_indian_stock_metadata():
    service = FinnhubService(
        client=FakeFinnhubClient({
            ("/quote", "RELIANCE.NS"): {"c": 2860.5, "pc": 2840.0, "d": 20.5, "dp": 0.7218, "v": 5_000_000},
            ("/stock/profile2", "RELIANCE.NS"): {
                "ticker": "RELIANCE.NS",
                "name": "Reliance Industries Ltd",
                "exchange": "National Stock Exchange of India",
                "country": "IN",
                "currency": "INR",
            },
        }),
        cache=NoopCache(),
    )

    result = await service.get_quote("RELIANCE.NS")

    assert result["symbol"] == "RELIANCE.NS"
    assert result["exchange"] == "National Stock Exchange of India"
    assert result["country"] == "IN"
    assert result["currency"] == "INR"


@pytest.mark.asyncio
async def test_invalid_symbol_returns_structured_error():
    service = FinnhubService(
        client=FakeFinnhubClient({
            ("/quote", "INVALID"): {"c": 0, "pc": 0, "d": None, "dp": None},
        }),
        cache=NoopCache(),
    )

    result = await service.get_quote("INVALID")

    assert result == {
        "error": {
            "code": "SYMBOL_NOT_FOUND",
            "message": "No quote data found for INVALID.",
        }
    }


@pytest.mark.asyncio
async def test_technical_indicators_from_yahoo_history(monkeypatch):
    monkeypatch.setattr(FinnhubService, "_download_yfinance_history", staticmethod(lambda symbol, period: history_frame()))
    service = FinnhubService(
        client=FakeFinnhubClient({}),
        cache=NoopCache(),
    )

    result = await service.get_technical_indicators("MSFT")

    assert result["symbol"] == "MSFT"
    assert result["sma_20"] is not None
    assert result["sma_50"] is not None
    assert result["sma_200"] is not None
    assert result["rsi"] is not None
    assert result["macd"] is not None
    assert result["signal_line"] is not None


@pytest.mark.asyncio
async def test_finnhub_client_rate_limit_response():
    transport = httpx.MockTransport(lambda request: httpx.Response(429, json={"error": "limit"}))
    async_client = httpx.AsyncClient(transport=transport, base_url="https://finnhub.io/api/v1")
    client = FinnhubClient(api_key="test-key", client=async_client, max_retries=0)

    result = await client.get("/quote", {"symbol": "AAPL"})
    await async_client.aclose()

    assert result["error"]["code"] == "RATE_LIMITED"


@pytest.mark.asyncio
async def test_finnhub_client_missing_api_key():
    client = FinnhubClient(api_key="")

    result = await client.get("/quote", {"symbol": "AAPL"})

    assert result["error"]["code"] == "MISSING_API_KEY"
