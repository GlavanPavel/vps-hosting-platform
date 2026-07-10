import jwt
from fastapi import APIRouter, Response, Request, HTTPException

from routers.deps import UowDep, CurrentUserDep
from schemas.user import UserCreate, UserLogin, UserResponse
from core.security import create_access_token, create_refresh_token, decode_token, hash_token
from core.config import config
from core.unit_of_work import UnitOfWork
from models.user import User
import services

auth_router = APIRouter(prefix="/auth", tags=["auth"])

_ACCESS_MAX_AGE = config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
_REFRESH_MAX_AGE = config.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


async def _issue_session(uow: UnitOfWork, user: User, response: Response) -> None:
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    user.refresh_token_hash = hash_token(refresh)
    await uow.commit()
    response.set_cookie(
        "access_token", access, max_age=_ACCESS_MAX_AGE, httponly=True,
        secure=config.COOKIE_SECURE, samesite=config.COOKIE_SAMESITE, path="/",
    )
    response.set_cookie(
        "refresh_token", refresh, max_age=_REFRESH_MAX_AGE, httponly=True,
        secure=config.COOKIE_SECURE, samesite=config.COOKIE_SAMESITE, path="/auth",
    )


def _clear_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/auth")


@auth_router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, uow: UowDep):
    return await services.register_user(uow=uow, data=data)


@auth_router.post("/login", response_model=UserResponse)
async def login(data: UserLogin, uow: UowDep, response: Response):
    user = await services.login_user(uow=uow, data=data)
    await _issue_session(uow, user, response)
    return user


@auth_router.post("/refresh", status_code=200)
async def refresh(request: Request, uow: UowDep, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        user_id = decode_token(token, "refresh")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = await uow.users.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or disabled")
    if not user.refresh_token_hash or hash_token(token) != user.refresh_token_hash:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    await _issue_session(uow, user, response)
    return {"message": "Token refreshed"}


@auth_router.post("/logout", status_code=200)
async def logout(request: Request, uow: UowDep, response: Response):
    token = request.cookies.get("refresh_token")
    if token:
        try:
            user = await uow.users.get_by_id(decode_token(token, "refresh"))
        except jwt.PyJWTError:
            user = None
        if user and user.refresh_token_hash:
            user.refresh_token_hash = None
            await uow.commit()
    _clear_cookies(response)
    return {"message": "Logged out"}


@auth_router.get("/me", response_model=UserResponse)
async def me(uow: UowDep, user_id: CurrentUserDep):
    return await services.get_user_profile(uow=uow, user_id=user_id)
