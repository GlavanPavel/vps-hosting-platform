from core.celery_app import celery_app
from domain.dispatcher import on
from domain.events import OrganizationDeletionRequested
from models.instance import Instance
from models.keypair import Keypair
from models.security_group import SecurityGroup, SecurityGroupRule
from models.network import Network, FloatingIP
from models.volume import Volume
from models.image import Image
from models.instance_event import InstanceEvent
from models.user import Organization, User
from tasks.common import SessionLocal, _os_connect


# event handlers

@on(OrganizationDeletionRequested)
def handle_org_deletion(event: OrganizationDeletionRequested) -> None:
    teardown_organization.delay(organization_id=event.organization_id)


# celery tasks

@celery_app.task
def teardown_organization(organization_id: int):
    print(f"[teardown_organization] tearing down org {organization_id}")
    conn = _os_connect()

    # collect the OpenStack ids from the DB
    with SessionLocal() as db:
        server_ids = [
            i.openstack_id for i in db.query(Instance)
            .filter(Instance.organization_id == organization_id).all() if i.openstack_id
        ]
        volume_ids = [
            v.openstack_volume_id for v in db.query(Volume)
            .filter(Volume.organization_id == organization_id).all() if v.openstack_volume_id
        ]
        fip_ids = [
            f.openstack_floatingip_id for f in db.query(FloatingIP)
            .filter(FloatingIP.organization_id == organization_id).all() if f.openstack_floatingip_id
        ]
        net_pairs = [
            (n.openstack_network_id, n.openstack_router_id) for n in db.query(Network)
            .filter(Network.organization_id == organization_id).all() if n.openstack_network_id
        ]
        sg_ids = [
            s.openstack_id for s in db.query(SecurityGroup)
            .filter(SecurityGroup.organization_id == organization_id).all() if s.openstack_id
        ]
        image_ids = [
            im.openstack_image_id for im in db.query(Image)
            .filter(Image.organization_id == organization_id).all() if im.openstack_image_id
        ]
        user_ids = [u.id for u in db.query(User).filter(User.organization_id == organization_id).all()]
        kp_names = [
            k.openstack_name for k in db.query(Keypair).filter(Keypair.user_id.in_(user_ids)).all()
            if k.openstack_name
        ] if user_ids else []

    # delete servers, then wait for them to be gone (so ports/SGs are free)
    for sid in server_ids:
        try:
            server = conn.compute.find_server(sid)
            if server:
                conn.compute.delete_server(server)
        except Exception as e:
            print(f"[teardown_organization] server {sid}: {e}")
    for sid in server_ids:
        try:
            server = conn.compute.find_server(sid)
            if server:
                conn.compute.wait_for_delete(server, wait=180)
        except Exception:
            pass

    # floating IPs
    for fid in fip_ids:
        try:
            conn.network.delete_ip(fid, ignore_missing=True)
        except Exception as e:
            print(f"[teardown_organization] floating ip {fid}: {e}")

    # volumes
    for vid in volume_ids:
        try:
            os_vol = conn.block_storage.find_volume(vid)
            if os_vol:
                conn.block_storage.delete_volume(os_vol, ignore_missing=True)
        except Exception as e:
            print(f"[teardown_organization] volume {vid}: {e}")

    # security groups
    for sgid in sg_ids:
        try:
            os_sg = conn.network.find_security_group(sgid)
            if os_sg:
                conn.network.delete_security_group(os_sg, ignore_missing=True)
        except Exception as e:
            print(f"[teardown_organization] security group {sgid}: {e}")

    # networks
    for net_id, router_id in net_pairs:
        try:
            if router_id:
                router = conn.network.find_router(router_id)
                if router:
                    for port in conn.network.ports(
                        device_id=router.id, device_owner="network:router_interface"
                    ):
                        try:
                            conn.network.remove_interface_from_router(
                                router, subnet_id=port.fixed_ips[0]["subnet_id"]
                            )
                        except Exception:
                            pass
                    conn.network.delete_router(router, ignore_missing=True)
            os_net = conn.network.find_network(net_id)
            if os_net:
                for subnet_id in os_net.subnet_ids:
                    conn.network.delete_subnet(subnet_id, ignore_missing=True)
                conn.network.delete_network(os_net, ignore_missing=True)
        except Exception as e:
            print(f"[teardown_organization] network {net_id}: {e}")

    # images
    for imid in image_ids:
        try:
            os_img = conn.image.find_image(imid)
            if os_img:
                conn.image.delete_image(os_img, ignore_missing=True)
        except Exception as e:
            print(f"[teardown_organization] image {imid}: {e}")

    # keypairs
    for name in kp_names:
        try:
            kp = conn.compute.find_keypair(name)
            if kp:
                conn.compute.delete_keypair(kp)
        except Exception as e:
            print(f"[teardown_organization] keypair {name}: {e}")

    # remove every DB row in FK-dependency order, then the org itself
    with SessionLocal() as db:
        inst_ids = [
            i.id for i in db.query(Instance).filter(Instance.organization_id == organization_id).all()
        ]
        if inst_ids:
            db.query(InstanceEvent).filter(
                InstanceEvent.instance_id.in_(inst_ids)
            ).delete(synchronize_session=False)
        for inst in db.query(Instance).filter(Instance.organization_id == organization_id).all():
            inst.security_groups.clear()
            db.delete(inst)
        db.flush()
        for vol in db.query(Volume).filter(Volume.organization_id == organization_id).all():
            db.delete(vol)
        for fip in db.query(FloatingIP).filter(FloatingIP.organization_id == organization_id).all():
            db.delete(fip)
        for img in db.query(Image).filter(Image.organization_id == organization_id).all():
            db.delete(img)
        db.flush()
        for sg in db.query(SecurityGroup).filter(SecurityGroup.organization_id == organization_id).all():
            for rule in db.query(SecurityGroupRule).filter(
                SecurityGroupRule.security_group_id == sg.id
            ).all():
                db.delete(rule)
            db.delete(sg)
        for net in db.query(Network).filter(Network.organization_id == organization_id).all():
            db.delete(net)  # subnets cascade via the relationship
        db.flush()
        users = db.query(User).filter(User.organization_id == organization_id).all()
        uids = [u.id for u in users]
        if uids:
            for kp in db.query(Keypair).filter(Keypair.user_id.in_(uids)).all():
                db.delete(kp)
        db.flush()
        for u in users:
            db.delete(u)
        org = db.query(Organization).filter(Organization.id == organization_id).first()
        if org:
            db.delete(org)
        db.commit()

    print(f"[teardown_organization] org {organization_id} fully removed")
    return {"status": "success", "organization_id": organization_id}
