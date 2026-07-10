from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.volume import Volume
from repositories.base import BaseRepository


class VolumeRepository(BaseRepository[Volume]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Volume)

    async def get_by_org(self, organization_id: int) -> list[Volume]:
        result = await self._session.execute(
            select(Volume).where(Volume.organization_id == organization_id)
        )
        return list(result.scalars().all())

    async def get_by_id_and_org(self, volume_id: int, organization_id: int) -> Volume | None:
        result = await self._session.execute(
            select(Volume).where(
                Volume.id == volume_id, Volume.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_ids_and_org(
        self, volume_ids: list[int], organization_id: int
    ) -> list[Volume]:
        if not volume_ids:
            return []
        result = await self._session.execute(
            select(Volume).where(
                Volume.id.in_(volume_ids), Volume.organization_id == organization_id
            )
        )
        return list(result.scalars().all())
