from fastapi import APIRouter
from routers.deps import UowDep, CurrentUserDep
from schemas.keypair import (
    KeypairCreate,
    KeypairGenerate,
    KeypairResponse,
    KeypairGenerateResponse,
)
import services

keypair_router = APIRouter(prefix="/keypairs", tags=["keypairs"])


@keypair_router.get("/", response_model=list[KeypairResponse])
async def list_keypairs(uow: UowDep, user_id: CurrentUserDep):
    return await services.list_keypairs(uow=uow, user_id=user_id)


@keypair_router.post("/", response_model=KeypairResponse, status_code=201)
async def create_keypair(data: KeypairCreate, uow: UowDep, user_id: CurrentUserDep):
    return await services.create_keypair(uow=uow, data=data, user_id=user_id)


@keypair_router.post("/generate", response_model=KeypairGenerateResponse, status_code=201)
async def generate_keypair(data: KeypairGenerate, uow: UowDep, user_id: CurrentUserDep):
    return await services.generate_keypair(uow=uow, data=data, user_id=user_id)


@keypair_router.delete("/{keypair_id}", status_code=200)
async def delete_keypair(keypair_id: int, uow: UowDep, user_id: CurrentUserDep):
    return await services.delete_keypair(uow=uow, keypair_id=keypair_id, user_id=user_id)
