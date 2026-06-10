"""
websocket/manager.py — WebSocket connection manager and real-time streaming.

Supports:
- Live stock price updates (broadcast to subscribers)
- Streaming AI analysis responses (SSE-style over WebSocket)
- Real-time alerts (price threshold notifications)

Connection model:
- Each user can have multiple WebSocket connections (e.g. multiple tabs)
- Connections are grouped by user_id and by symbol subscription
- Price update loop runs as a background task
"""

import asyncio
import json
from datetime import datetime
from typing import Optional
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.websockets import WebSocketState

from auth.jwt_handler import verify_access_token
from core.logging import logger

websocket_router = APIRouter()


class ConnectionManager:
    """
    Manages active WebSocket connections.

    Uses two indexes:
    - user_connections: user_id → set of WebSocket objects (all user's tabs)
    - symbol_subscribers: symbol → set of user_ids (who's watching this symbol)
    """

    def __init__(self):
        # user_id → list of websocket connections
        self.user_connections: dict[str, list[WebSocket]] = defaultdict(list)
        # symbol → set of user_ids watching it
        self.symbol_subscribers: dict[str, set[str]] = defaultdict(set)
        # Track active price update tasks
        self._price_tasks: dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self.user_connections[user_id].append(websocket)
        logger.info("WebSocket connected", user_id=user_id,
                    total_connections=sum(len(v) for v in self.user_connections.values()))

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        connections = self.user_connections.get(user_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            del self.user_connections[user_id]
        logger.info("WebSocket disconnected", user_id=user_id)

    async def send_to_user(self, user_id: str, message: dict) -> None:
        """Send a message to ALL connections for a user."""
        connections = self.user_connections.get(user_id, [])
        dead_connections = []
        for ws in connections:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(json.dumps(message))
            except Exception:
                dead_connections.append(ws)
        for ws in dead_connections:
            connections.remove(ws)

    async def broadcast_price_update(self, symbol: str, price_data: dict) -> None:
        """Broadcast a price update to all users watching this symbol."""
        subscribers = self.symbol_subscribers.get(symbol, set())
        message = {
            "type": "price_update",
            "symbol": symbol,
            "data": price_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        tasks = [self.send_to_user(user_id, message) for user_id in list(subscribers)]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def subscribe_to_symbol(self, user_id: str, symbol: str) -> None:
        self.symbol_subscribers[symbol.upper()].add(user_id)
        logger.debug("Symbol subscription added", user_id=user_id, symbol=symbol)

        # Start price update loop if not already running
        if symbol.upper() not in self._price_tasks or self._price_tasks[symbol.upper()].done():
            task = asyncio.create_task(self._price_update_loop(symbol.upper()))
            self._price_tasks[symbol.upper()] = task

    def unsubscribe_from_symbol(self, user_id: str, symbol: str) -> None:
        self.symbol_subscribers[symbol.upper()].discard(user_id)
        if not self.symbol_subscribers[symbol.upper()]:
            # No more subscribers — cancel the update task
            task = self._price_tasks.get(symbol.upper())
            if task and not task.done():
                task.cancel()
            del self.symbol_subscribers[symbol.upper()]

    async def _price_update_loop(self, symbol: str, interval_seconds: int = 30) -> None:
        """Background task: poll for price updates every N seconds."""
        from tools.financial_tools import get_stock_price_tool
        logger.info("Price update loop started", symbol=symbol)
        while self.symbol_subscribers.get(symbol):
            try:
                price_data = await get_stock_price_tool(symbol)
                await self.broadcast_price_update(symbol, price_data)
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Price update loop error", symbol=symbol, error=str(e))
                await asyncio.sleep(interval_seconds)
        logger.info("Price update loop stopped", symbol=symbol)

    async def stream_analysis(
        self, websocket: WebSocket, user_id: str, symbol: str, risk_tolerance: str
    ) -> None:
        """Stream a multi-agent analysis progress over WebSocket."""
        from services.analysis_service import AnalysisService
        from schemas.schemas import StockAnalysisRequest

        async def send_event(event_type: str, data: dict):
            await websocket.send_text(json.dumps({
                "type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }))

        await send_event("analysis_started", {"symbol": symbol, "message": "Starting multi-agent analysis..."})

        # Simulate streaming progress events (in production, use callbacks/hooks)
        steps = [
            ("memory_retrieval", "Retrieving your investment history..."),
            ("financial", f"Fetching price and technical data for {symbol}..."),
            ("news", f"Analyzing recent news for {symbol}..."),
            ("sentiment", "Computing market sentiment..."),
            ("risk", "Assessing risk profile..."),
            ("reasoning", "Synthesizing all agent outputs..."),
            ("recommendation", "Generating investment recommendation..."),
        ]

        for step_name, step_msg in steps:
            await send_event("progress", {"step": step_name, "message": step_msg})
            await asyncio.sleep(0.5)  # Simulate processing delay

        # Run actual analysis
        try:
            from database.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                service = AnalysisService(db)
                request = StockAnalysisRequest(symbol=symbol)
                result = await service.analyze_stock(
                    symbol=symbol,
                    user_id=user_id,
                    user_risk_tolerance=risk_tolerance,
                    request=request,
                )

            await send_event("analysis_complete", {
                "symbol": symbol,
                "result": result.model_dump(mode="json"),
            })
        except Exception as e:
            await send_event("error", {"message": str(e)})


# Module-level singleton
manager = ConnectionManager()


# ─── WebSocket Route ──────────────────────────────────────────────────────────

@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
    """
    Main WebSocket endpoint.

    Client message format:
    {"action": "subscribe", "symbol": "AAPL"}
    {"action": "unsubscribe", "symbol": "AAPL"}
    {"action": "analyze", "symbol": "AAPL"}
    {"action": "ping"}
    """
    # Authenticate via query param token
    payload = verify_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    await manager.connect(websocket, user_id)
    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": "WebSocket connection established",
        "user_id": user_id,
    }))

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
                continue

            action = msg.get("action")
            symbol = msg.get("symbol", "").upper()

            if action == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

            elif action == "subscribe" and symbol:
                manager.subscribe_to_symbol(user_id, symbol)
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "symbol": symbol,
                    "message": f"Subscribed to real-time updates for {symbol}",
                }))

            elif action == "unsubscribe" and symbol:
                manager.unsubscribe_from_symbol(user_id, symbol)
                await websocket.send_text(json.dumps({
                    "type": "unsubscribed",
                    "symbol": symbol,
                }))

            elif action == "analyze" and symbol:
                # Stream analysis progress over this WebSocket
                from database.session import AsyncSessionLocal
                async with AsyncSessionLocal() as db:
                    from database.repositories.user_repository import UserRepository
                    repo = UserRepository(db)
                    user = await repo.get_by_id(user_id)
                    risk_tolerance = (user.risk_tolerance if user else None) or "moderate"
                await manager.stream_analysis(websocket, user_id, symbol, risk_tolerance)

            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Unknown action: {action}",
                }))

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error("WebSocket error", user_id=user_id, error=str(e))
        manager.disconnect(websocket, user_id)
