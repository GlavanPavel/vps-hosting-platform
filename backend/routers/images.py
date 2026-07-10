from fastapi import APIRouter, Depends
from routers.deps import UowDep, CurrentUserDep, require_permission
from schemas.image import ImageCreate, ImageResponse, ImageVisibility
import services

image_router = APIRouter(prefix="/images", tags=["images"])


@image_router.get("/", response_model=list[ImageResponse])
async def list_images(uow: UowDep, user_id: CurrentUserDep, include_public: bool = False):
    user = await uow.users.get_by_id(user_id)
    return await services.list_images(
        uow=uow, organization_id=user.organization_id, include_public=include_public
    )


@image_router.post("/", response_model=ImageResponse, status_code=201)
async def create_image(data: ImageCreate, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.create_image(uow=uow, data=data, organization_id=user.organization_id)


@image_router.post(
    "/{image_id}/visibility", response_model=ImageResponse,
    dependencies=[Depends(require_permission("image:publish"))],
)
async def set_image_visibility(
    image_id: int, data: ImageVisibility, uow: UowDep, user_id: CurrentUserDep
):
    user = await uow.users.get_by_id(user_id)
    return await services.set_image_visibility(
        uow=uow, image_id=image_id, is_public=data.is_public,
        organization_id=user.organization_id,
    )


@image_router.delete(
    "/{image_id}", status_code=200,
    dependencies=[Depends(require_permission("image:delete"))],
)
async def delete_image(image_id: int, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.delete_image(
        uow=uow, image_id=image_id, organization_id=user.organization_id
    )
