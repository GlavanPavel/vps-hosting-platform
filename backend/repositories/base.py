from typing import Generic, TypeVar, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession, model: Type[ModelT]):
        self._session = session
        self._model = model

    async def get_by_id(self, id: int) -> ModelT | None:
        return await self._session.get(self._model, id)

    async def get_all(self) -> list[ModelT]:
        result = await self._session.execute(select(self._model))
        return list(result.scalars().all())

    async def add(self, entity: ModelT) -> ModelT:
        self._session.add(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self._session.delete(entity)
