"""LangChain-compatible financial tools backed by Finnhub market data."""

import asyncio

from langchain.tools import tool

from services.market_data import FinnhubService


async def get_stock_price_tool(symbol: str) -> dict:
    return await FinnhubService().get_quote(symbol)


async def get_historical_data(symbol: str, period: str = "1y") -> dict:
    return await FinnhubService().get_historical_summary(symbol, period)


async def calculate_technical_indicators(symbol: str, period: str = "1y") -> dict:
    return await FinnhubService().get_technical_indicators(symbol, period)


async def calculate_volatility(symbol: str, period: str = "1y") -> dict:
    return await FinnhubService().get_volatility(symbol, period)


@tool
def get_stock_price(symbol: str) -> str:
    """Get the current stock price and key metrics for a stock ticker symbol."""
    return str(asyncio.run(get_stock_price_tool(symbol)))


@tool
def get_technical_analysis(symbol: str) -> str:
    """Calculate RSI, MACD, SMA, and signal-line indicators for a stock ticker symbol."""
    return str(asyncio.run(calculate_technical_indicators(symbol)))


@tool
def get_stock_volatility(symbol: str) -> str:
    """Calculate volatility, max drawdown, and Sharpe ratio for a stock ticker symbol."""
    return str(asyncio.run(calculate_volatility(symbol)))


@tool
def get_historical_prices(symbol_and_period: str) -> str:
    """Get historical price summary. Input format: 'SYMBOL PERIOD' (for example, 'AAPL 1y')."""
    parts = symbol_and_period.strip().split()
    symbol = parts[0] if parts else "AAPL"
    period = parts[1] if len(parts) > 1 else "1y"
    return str(asyncio.run(get_historical_data(symbol, period)))


ALL_FINANCIAL_TOOLS = [
    get_stock_price,
    get_technical_analysis,
    get_stock_volatility,
    get_historical_prices,
]
