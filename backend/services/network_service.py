from fastapi import HTTPException
from core.unit_of_work import UnitOfWork
from models.network import Network, Subnet
from schemas.network import NetworkCreate, NetworkResponse
from domain.events import (
    NetworkProvisioningStarted,
    SubnetProvisioningStarted,
    NetworkDeletionRequested,
)
from domain.dispatcher import dispatch


async def create_network(
    uow: UnitOfWork, data: NetworkCreate, organization_id: int
) -> NetworkResponse:
    network = Network(organization_id=organization_id, name=data.name)
    await uow.networks.add(network)
    await uow.commit()
    await uow.refresh(network)

    # Emit one event per subnet so Celery can provision them in OS
    for subnet_data in data.subnets:
        subnet = Subnet(network_id=network.id, name=subnet_data.name, cidr=subnet_data.cidr)
        await uow.subnets.add(subnet)
        await uow.commit()
        await uow.refresh(subnet)

    dispatch(NetworkProvisioningStarted(
        network_id=network.id,
        organization_id=organization_id,
        name=network.name,
    ))

    # re-fetch with subnets eager-loaded — lazy loading is not allowed in async context
    network = await uow.networks.get_by_id_and_org(network.id, organization_id)
    return NetworkResponse.model_validate(network)


async def list_networks(uow: UnitOfWork, organization_id: int) -> list[NetworkResponse]:
    networks = await uow.networks.get_by_org(organization_id)
    return [NetworkResponse.model_validate(n) for n in networks]


async def delete_network(uow: UnitOfWork, network_id: int, organization_id: int) -> dict:
    network = await uow.networks.get_by_id_and_org(network_id, organization_id)
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")

    attached = await uow.instances.count_by_subnet_ids([s.id for s in network.subnets])
    if attached:
        raise HTTPException(
            status_code=409,
            detail=f"Network has {attached} instance(s) attached — delete them first",
        )

    # capture before the row (and its cascade-deleted subnets) is gone
    openstack_network_id = network.openstack_network_id
    openstack_router_id = network.openstack_router_id
    await uow.networks.delete(network)
    await uow.commit()

    # may be None if Celery never finished provisioning
    if openstack_network_id:
        dispatch(NetworkDeletionRequested(
            openstack_network_id=openstack_network_id,
            openstack_router_id=openstack_router_id,
        ))

    return {"message": "Network deleted"}
