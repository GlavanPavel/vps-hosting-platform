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
    VolumeRepository,
    ImageRepository,
    CloudStatsRepository,
    QuotaRepository,
    InstanceEventRepository,
)


class UnitOfWork:

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
        self.volumes = VolumeRepository(session)
        self.images = ImageRepository(session)
        self.cloud_stats = CloudStatsRepository(session)
        self.quotas = QuotaRepository(session)
        self.instance_events = InstanceEventRepository(session)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def refresh(self, entity: object) -> None:
        await self._session.refresh(entity)
