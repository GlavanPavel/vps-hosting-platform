from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.cloud_stats import CloudStats
from repositories.base import BaseRepository


class CloudStatsRepository(BaseRepository[CloudStats]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, CloudStats)

    async def get_latest(self) -> CloudStats | None:
        result = await self._session.execute(
            select(CloudStats).order_by(CloudStats.id.desc()).limit(1)
        )
        return result.scalar_one_or_none()
