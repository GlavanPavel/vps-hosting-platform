from fastapi import HTTPException
from core.unit_of_work import UnitOfWork
from models.security_group import SecurityGroup, SecurityGroupRule
from schemas.security_group import SecurityGroupCreate, SecurityGroupResponse


async def create_security_group(
    uow: UnitOfWork, data: SecurityGroupCreate, organization_id: int
) -> SecurityGroupResponse:
    sg = SecurityGroup(
        organization_id=organization_id,
        name=data.name,
        description=data.description,
    )
    sg.rules = [
        SecurityGroupRule(
            direction=r.direction,
            protocol=r.protocol,
            port_range_min=r.port_range_min,
            port_range_max=r.port_range_max,
            remote_ip_prefix=r.remote_ip_prefix,
        )
        for r in data.rules
    ]
    await uow.security_groups.add(sg)
    await uow.commit()
    await uow.refresh(sg)
    return SecurityGroupResponse.model_validate(sg)


async def list_security_groups(uow: UnitOfWork, organization_id: int) -> list[SecurityGroupResponse]:
    groups = await uow.security_groups.get_by_org(organization_id)
    return [SecurityGroupResponse.model_validate(sg) for sg in groups]


async def delete_security_group(
    uow: UnitOfWork, sg_id: int, organization_id: int
) -> dict:
    sg = await uow.security_groups.get_by_id_and_org(sg_id, organization_id)
    if not sg:
        raise HTTPException(status_code=404, detail="Security group not found")
    await uow.security_groups.delete(sg)
    await uow.commit()
    return {"message": "Security group deleted"}
