from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.security import decode_token
from core.permissions import has_permission
from core.unit_of_work import UnitOfWork
from models.user import User


async def get_uow(session: AsyncSession = Depends(get_db_session)) -> UnitOfWork:
    return UnitOfWork(session)


async def get_current_user_id(request: Request) -> int:
    token = request.cookies.get("access_token")
    if not token:
        header = request.headers.get("Authorization", "")
        if header.lower().startswith("bearer "):
            token = header[7:]
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return decode_token(token, "access")
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


UowDep = Annotated[UnitOfWork, Depends(get_uow)]
CurrentUserDep = Annotated[int, Depends(get_current_user_id)]


async def get_current_user(
    uow: UnitOfWork = Depends(get_uow),
    user_id: int = Depends(get_current_user_id),
) -> User:
    user = await uow.users.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or disabled")
    return user


CurrentUserModelDep = Annotated[User, Depends(get_current_user)]


def require_permission(permission: str):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if not has_permission(user.role, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Your role ('{user.role}') is not allowed to perform this action ({permission})",
            )
        return user
    return checker


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not has_permission(user.role, "admin:view"):
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


AdminUserDep = Annotated[User, Depends(require_admin)]
