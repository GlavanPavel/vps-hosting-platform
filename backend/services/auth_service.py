from fastapi import HTTPException
from core.unit_of_work import UnitOfWork
from core.security import hash_password, verify_password
from models.user import User, Organization
from schemas.user import UserCreate, UserLogin, UserResponse


async def register_user(uow: UnitOfWork, data: UserCreate) -> UserResponse:
    existing_user = await uow.users.get_by_email(data.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    existing_org = await uow.organizations.get_by_name(data.organization_name)
    if existing_org:
        raise HTTPException(status_code=409, detail="An organization with this name already exists")

    organization = Organization(name=data.organization_name)
    await uow.organizations.add(organization)
    # flush via commit so the org gets an id before the user row references it
    await uow.commit()
    await uow.refresh(organization)

    user = User(
        organization_id=organization.id,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    await uow.users.add(user)
    await uow.commit()
    await uow.refresh(user)
    return UserResponse.model_validate(user)


async def login_user(uow: UnitOfWork, data: UserLogin) -> User:
    user = await uow.users.get_by_email(data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is disabled")
    return user


async def get_user_profile(uow: UnitOfWork, user_id: int) -> UserResponse:
    user = await uow.users.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)
