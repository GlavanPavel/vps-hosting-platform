from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.quota import Quota
from repositories.base import BaseRepository


class QuotaRepository(BaseRepository[Quota]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Quota)

    async def get_by_org(self, organization_id: int) -> Quota | None:
        result = await self._session.execute(
            select(Quota).where(Quota.organization_id == organization_id)
        )
        return result.scalar_one_or_none()
