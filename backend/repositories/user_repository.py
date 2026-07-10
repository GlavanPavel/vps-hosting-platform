from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User, Organization
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id_and_org(self, user_id: int, organization_id: int) -> User | None:
        result = await self._session.execute(
            select(User).where(User.id == user_id, User.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def get_by_org(self, organization_id: int) -> list[User]:
        result = await self._session.execute(
            select(User).where(User.organization_id == organization_id).order_by(User.created_at)
        )
        return list(result.scalars().all())

    async def count_active_owners(self, organization_id: int) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(User).where(
                User.organization_id == organization_id,
                User.role == "owner",
                User.is_active.is_(True),
            )
        )
        return int(result.scalar_one())


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Organization)

    async def get_by_name(self, name: str) -> Organization | None:
        result = await self._session.execute(
            select(Organization).where(Organization.name == name)
        )
        return result.scalar_one_or_none()
