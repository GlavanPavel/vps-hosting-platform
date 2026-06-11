from sqlalchemy.ext.asyncio import AsyncSession
from repositories import (
    UserRepository,
    OrganizationRepository,
    InstanceRepository,
    KeypairRepository,
    SecurityGroupRepository,
    SecurityGroupRuleRepository,
    NetworkRepository,
    SubnetRepository,
    FloatingIPRepository,
)


class UnitOfWork:
    """Bundles all repositories under a single session so a service method
    can span multiple repos and commit once."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self.users = UserRepository(session)
        self.organizations = OrganizationRepository(session)
        self.instances = InstanceRepository(session)
        self.keypairs = KeypairRepository(session)
        self.security_groups = SecurityGroupRepository(session)
        self.security_group_rules = SecurityGroupRuleRepository(session)
        self.networks = NetworkRepository(session)
        self.subnets = SubnetRepository(session)
        self.floating_ips = FloatingIPRepository(session)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def refresh(self, entity: object) -> None:
        await self._session.refresh(entity)
