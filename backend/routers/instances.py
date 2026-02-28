from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db_session
import backend.services as services

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
router = APIRouter(prefix="/instances", tags=["instances"])

@router.get("/")
async def get_instances(db: SessionDep):
    return await services.get_all_instances(db=db)


@router.post("/")
async def create_vm_endpoint(
        db: SessionDep
):
    return await services.create_instance(db=db)

@router.delete("/{instance_id}")
async def delete_vm_endpoint(
    instance_id: int,
    db: SessionDep
):
    return await services.delete_instance(db=db, instance_id=instance_id)