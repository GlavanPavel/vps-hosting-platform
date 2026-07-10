from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from models.network import Network, Subnet, FloatingIP
from repositories.base import BaseRepository


class NetworkRepository(BaseRepository[Network]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Network)

    async def get_by_org(self, organization_id: int) -> list[Network]:
        result = await self._session.execute(
            select(Network)
            .where(Network.organization_id == organization_id)
            .options(selectinload(Network.subnets))
        )
        return list(result.scalars().all())

    async def get_by_id_and_org(self, network_id: int, organization_id: int) -> Network | None:
        result = await self._session.execute(
            select(Network)
            .where(Network.id == network_id, Network.organization_id == organization_id)
            .options(selectinload(Network.subnets))
        )
        return result.scalar_one_or_none()


class SubnetRepository(BaseRepository[Subnet]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Subnet)

    async def get_by_id_and_org(self, subnet_id: int, organization_id: int) -> Subnet | None:
        result = await self._session.execute(
            select(Subnet)
            .join(Subnet.network)
            .where(Subnet.id == subnet_id, Network.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def get_by_network(self, network_id: int) -> list[Subnet]:
        result = await self._session.execute(
            select(Subnet).where(Subnet.network_id == network_id)
        )
        return list(result.scalars().all())


class FloatingIPRepository(BaseRepository[FloatingIP]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, FloatingIP)

    async def get_by_org(self, organization_id: int) -> list[FloatingIP]:
        result = await self._session.execute(
            select(FloatingIP)
            .where(FloatingIP.organization_id == organization_id)
            .order_by(FloatingIP.id)
        )
        return list(result.scalars().all())

    async def get_by_id_and_org(self, floating_ip_id: int, organization_id: int) -> FloatingIP | None:
        result = await self._session.execute(
            select(FloatingIP).where(
                FloatingIP.id == floating_ip_id,
                FloatingIP.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_instance(self, instance_id: int) -> FloatingIP | None:
        result = await self._session.execute(
            select(FloatingIP).where(FloatingIP.instance_id == instance_id)
        )
        return result.scalar_one_or_none()
