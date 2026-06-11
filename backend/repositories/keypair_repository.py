from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.keypair import Keypair
from repositories.base import BaseRepository


class KeypairRepository(BaseRepository[Keypair]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Keypair)

    async def get_by_user(self, user_id: int) -> list[Keypair]:
        result = await self._session.execute(
            select(Keypair).where(Keypair.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_by_id_and_user(self, keypair_id: int, user_id: int) -> Keypair | None:
        result = await self._session.execute(
            select(Keypair).where(Keypair.id == keypair_id, Keypair.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name_and_user(self, name: str, user_id: int) -> Keypair | None:
        result = await self._session.execute(
            select(Keypair).where(Keypair.name == name, Keypair.user_id == user_id)
        )
        return result.scalar_one_or_none()
