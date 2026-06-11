from fastapi import HTTPException
from core.unit_of_work import UnitOfWork
from models.network import Network, Subnet
from schemas.network import NetworkCreate, NetworkResponse
from domain.events import NetworkProvisioningStarted, SubnetProvisioningStarted
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

    await uow.refresh(network)
    return NetworkResponse.model_validate(network)


async def list_networks(uow: UnitOfWork, organization_id: int) -> list[NetworkResponse]:
    networks = await uow.networks.get_by_org(organization_id)
    return [NetworkResponse.model_validate(n) for n in networks]


async def delete_network(uow: UnitOfWork, network_id: int, organization_id: int) -> dict:
    network = await uow.networks.get_by_id_and_org(network_id, organization_id)
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    await uow.networks.delete(network)
    await uow.commit()
    return {"message": "Network deleted"}
