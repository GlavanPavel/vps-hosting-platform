from fastapi import HTTPException
from core.unit_of_work import UnitOfWork
from core.security import hash_password
from models.user import User
from schemas.user import MemberCreate, MemberUpdate, UserResponse


async def list_members(uow: UnitOfWork, organization_id: int) -> list[UserResponse]:
    members = await uow.users.get_by_org(organization_id)
    return [UserResponse.model_validate(m) for m in members]


async def create_member(
    uow: UnitOfWork, data: MemberCreate, organization_id: int
) -> UserResponse:
    existing = await uow.users.get_by_email(data.email)
    if existing:
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    member = User(
        organization_id=organization_id,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
    )
    await uow.users.add(member)
    await uow.commit()
    await uow.refresh(member)
    return UserResponse.model_validate(member)


async def update_member(
    uow: UnitOfWork, member_id: int, data: MemberUpdate, organization_id: int, actor_id: int
) -> UserResponse:
    member = await uow.users.get_by_id_and_org(member_id, organization_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    new_role = data.role if data.role is not None else member.role
    new_active = data.is_active if data.is_active is not None else member.is_active

    # an owner can't lock themselves out of their own account
    if member.id == actor_id and data.is_active is False:
        raise HTTPException(status_code=409, detail="You cannot deactivate your own account")

    # never leave the organization without an active owner
    removing_owner_powers = (
        member.role == "owner" and member.is_active and (new_role != "owner" or new_active is False)
    )
    if removing_owner_powers and await uow.users.count_active_owners(organization_id) <= 1:
        raise HTTPException(
            status_code=409, detail="The organization must keep at least one active owner"
        )

    if data.role is not None:
        member.role = data.role
    if data.is_active is not None:
        member.is_active = data.is_active
    await uow.commit()
    await uow.refresh(member)
    return UserResponse.model_validate(member)
