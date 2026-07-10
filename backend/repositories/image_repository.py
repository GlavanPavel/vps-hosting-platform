from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from models.image import Image
from repositories.base import BaseRepository


class ImageRepository(BaseRepository[Image]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Image)

    async def get_by_org(self, organization_id: int) -> list[Image]:
        result = await self._session.execute(
            select(Image).where(Image.organization_id == organization_id)
        )
        return list(result.scalars().all())

    async def get_visible_to_org(self, organization_id: int) -> list[Image]:
        result = await self._session.execute(
            select(Image).where(
                or_(Image.organization_id == organization_id, Image.is_public.is_(True))
            )
        )
        return list(result.scalars().all())

    async def get_by_id_and_org(self, image_id: int, organization_id: int) -> Image | None:
        result = await self._session.execute(
            select(Image).where(
                Image.id == image_id, Image.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()
