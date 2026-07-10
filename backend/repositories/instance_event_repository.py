from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.instance_event import InstanceEvent
from repositories.base import BaseRepository


class InstanceEventRepository(BaseRepository[InstanceEvent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, InstanceEvent)

    async def get_by_instance(self, instance_id: int, limit: int = 100) -> list[InstanceEvent]:
        result = await self._session.execute(
            select(InstanceEvent)
            .where(InstanceEvent.instance_id == instance_id)
            .order_by(InstanceEvent.created_at.desc(), InstanceEvent.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
