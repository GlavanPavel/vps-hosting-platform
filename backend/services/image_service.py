from fastapi import HTTPException
from core.unit_of_work import UnitOfWork
from models.image import Image
from schemas.image import ImageCreate, ImageResponse
from domain.events import (
    ImageCreationRequested,
    ImageDeletionRequested,
    ImageVisibilityChangeRequested,
)
from domain.dispatcher import dispatch


async def create_image(
    uow: UnitOfWork, data: ImageCreate, organization_id: int
) -> ImageResponse:
    image = Image(
        organization_id=organization_id,
        name=data.name,
        source_url=data.source_url,
        disk_format=data.disk_format,
        status="queued",
    )
    await uow.images.add(image)
    await uow.commit()
    await uow.refresh(image)

    dispatch(ImageCreationRequested(
        image_id=image.id,
        name=image.name,
        source_url=image.source_url,
        disk_format=image.disk_format,
    ))
    return ImageResponse.model_validate(image)


async def list_images(
    uow: UnitOfWork, organization_id: int, include_public: bool = False
) -> list[ImageResponse]:
    if include_public:
        images = await uow.images.get_visible_to_org(organization_id)
    else:
        images = await uow.images.get_by_org(organization_id)
    return [ImageResponse.model_validate(i) for i in images]


async def set_image_visibility(
    uow: UnitOfWork, image_id: int, is_public: bool, organization_id: int
) -> ImageResponse:
    image = await uow.images.get_by_id_and_org(image_id, organization_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if not image.openstack_image_id or image.status != "active":
        raise HTTPException(
            status_code=409, detail="Only an active image can change visibility"
        )

    image.is_public = is_public
    await uow.commit()
    await uow.refresh(image)

    dispatch(ImageVisibilityChangeRequested(
        image_id=image.id,
        openstack_image_id=image.openstack_image_id,
        is_public=is_public,
    ))
    return ImageResponse.model_validate(image)


async def delete_image(uow: UnitOfWork, image_id: int, organization_id: int) -> dict:
    image = await uow.images.get_by_id_and_org(image_id, organization_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    openstack_image_id = image.openstack_image_id
    if openstack_image_id:
        image.status = "deleting"
        await uow.commit()
        dispatch(ImageDeletionRequested(
            image_id=image.id, openstack_image_id=openstack_image_id
        ))
        return {"message": "Image deletion requested"}

    # never made it into Glance (still queued/importing/ERROR) — safe to hard-delete
    await uow.images.delete(image)
    await uow.commit()
    return {"message": "Image removed"}
