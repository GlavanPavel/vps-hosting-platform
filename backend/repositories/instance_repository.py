from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from models.instance import Instance
from repositories.base import BaseRepository


class InstanceRepository(BaseRepository[Instance]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Instance)

    async def get_by_org(self, organization_id: int) -> list[Instance]:
        result = await self._session.execute(
            select(Instance)
            .where(Instance.organization_id == organization_id)
            .options(
                selectinload(Instance.keypair),
                selectinload(Instance.subnet),
                selectinload(Instance.security_groups),
                selectinload(Instance.floating_ip),
            )
        )
        return list(result.scalars().all())

    async def get_by_id_and_org(self, instance_id: int, organization_id: int) -> Instance | None:
        result = await self._session.execute(
            select(Instance)
            .where(Instance.id == instance_id, Instance.organization_id == organization_id)
            .options(
                selectinload(Instance.keypair),
                selectinload(Instance.subnet),
                selectinload(Instance.security_groups),
                selectinload(Instance.floating_ip),
            )
        )
        return result.scalar_one_or_none()
