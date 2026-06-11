"""Shared FastAPI dependencies.

get_current_user is a temporary stub that returns a hardcoded user_id.
Replace this with a real JWT dependency when auth is implemented.
"""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db_session
from core.unit_of_work import UnitOfWork


async def get_uow(session: AsyncSession = Depends(get_db_session)) -> UnitOfWork:
    return UnitOfWork(session)


# TODO: replace with JWT bearer dependency
async def get_current_user_id() -> int:
    return 1


UowDep = Annotated[UnitOfWork, Depends(get_uow)]
CurrentUserDep = Annotated[int, Depends(get_current_user_id)]
