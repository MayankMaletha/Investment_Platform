"""database/repositories/chat_repository.py — Chat history data access."""

from typing import Sequence
from sqlalchemy import select, delete, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.models import ChatHistory
from database.repositories.base import BaseRepository


class ChatRepository(BaseRepository[ChatHistory]):
    def __init__(self, session: AsyncSession):
        super().__init__(ChatHistory, session)

    async def get_session_history(self, user_id: str, session_id: str, limit: int = 20) -> Sequence[ChatHistory]:
        result = await self.session.execute(
            select(ChatHistory)
            .where(ChatHistory.user_id == user_id, ChatHistory.session_id == session_id)
            .order_by(ChatHistory.created_at.asc()).limit(limit)
        )
        return result.scalars().all()

    async def get_user_sessions(self, user_id: str) -> Sequence[str]:
        result = await self.session.execute(
            select(distinct(ChatHistory.session_id)).where(ChatHistory.user_id == user_id)
        )
        return result.scalars().all()

    async def clear_session(self, user_id: str, session_id: str) -> int:
        result = await self.session.execute(
            delete(ChatHistory).where(ChatHistory.user_id == user_id, ChatHistory.session_id == session_id)
        )
        return result.rowcount
