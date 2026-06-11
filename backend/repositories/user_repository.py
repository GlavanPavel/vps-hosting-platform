from sqlalchemy import select
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


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Organization)

    async def get_by_name(self, name: str) -> Organization | None:
        result = await self._session.execute(
            select(Organization).where(Organization.name == name)
        )
        return result.scalar_one_or_none()
