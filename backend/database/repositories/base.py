"""database/repositories/base.py — Generic async repository."""

from typing import Any, Generic, Optional, Sequence, Type, TypeVar
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, record_id: Any) -> Optional[ModelType]:
        result = await self.session.execute(select(self.model).where(self.model.id == record_id))
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[ModelType]:
        result = await self.session.execute(select(self.model).limit(limit).offset(offset))
        return result.scalars().all()

    async def create(self, **kwargs: Any) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, record_id: Any, **kwargs: Any) -> Optional[ModelType]:
        await self.session.execute(update(self.model).where(self.model.id == record_id).values(**kwargs))
        return await self.get_by_id(record_id)

    async def delete(self, record_id: Any) -> bool:
        result = await self.session.execute(delete(self.model).where(self.model.id == record_id))
        return result.rowcount > 0
