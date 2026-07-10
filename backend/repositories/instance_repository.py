from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from models.instance import Instance
from models.network import Subnet
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
                # also pull in the parent network so the detail view can name it
                selectinload(Instance.subnet).selectinload(Subnet.network),
                selectinload(Instance.security_groups),
                selectinload(Instance.floating_ip),
                selectinload(Instance.volumes),
            )
        )
        return result.scalar_one_or_none()

    async def count_by_subnet_ids(self, subnet_ids: list[int]) -> int:
        if not subnet_ids:
            return 0
        result = await self._session.execute(
            select(func.count())
            .select_from(Instance)
            .where(Instance.subnet_id.in_(subnet_ids))
        )
        return result.scalar_one()
