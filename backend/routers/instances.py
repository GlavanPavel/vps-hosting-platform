from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
import services as services
from schemas import InstanceRequest

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
router = APIRouter(prefix="/instances", tags=["instances"])

@router.get("/")
async def get_instances(db: SessionDep):
    return await services.get_all_instances(db=db)


@router.post("/")
async def create_vm_endpoint(
        instance_data: InstanceRequest,
        db: SessionDep
):
    return await services.create_instance(db=db, instance_data=instance_data)
@router.delete("/{instance_id}")
async def delete_vm_endpoint(
    instance_id: int,
    db: SessionDep
):
    return await services.delete_instance(db=db, instance_id=instance_id)