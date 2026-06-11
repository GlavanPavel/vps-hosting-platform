from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from models.security_group import SecurityGroup, SecurityGroupRule
from repositories.base import BaseRepository


class SecurityGroupRepository(BaseRepository[SecurityGroup]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SecurityGroup)

    async def get_by_org(self, organization_id: int) -> list[SecurityGroup]:
        result = await self._session.execute(
            select(SecurityGroup)
            .where(SecurityGroup.organization_id == organization_id)
            .options(selectinload(SecurityGroup.rules))
        )
        return list(result.scalars().all())

    async def get_by_id_and_org(self, sg_id: int, organization_id: int) -> SecurityGroup | None:
        result = await self._session.execute(
            select(SecurityGroup)
            .where(SecurityGroup.id == sg_id, SecurityGroup.organization_id == organization_id)
            .options(selectinload(SecurityGroup.rules))
        )
        return result.scalar_one_or_none()

    async def get_by_ids_and_org(
        self, sg_ids: list[int], organization_id: int
    ) -> list[SecurityGroup]:
        result = await self._session.execute(
            select(SecurityGroup)
            .where(
                SecurityGroup.id.in_(sg_ids),
                SecurityGroup.organization_id == organization_id,
            )
            .options(selectinload(SecurityGroup.rules))
        )
        return list(result.scalars().all())


class SecurityGroupRuleRepository(BaseRepository[SecurityGroupRule]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SecurityGroupRule)
