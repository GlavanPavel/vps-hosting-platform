import pytest

from conftest import (
    ASSIGN_FIP,
    FLAVOR,
    IMAGE,
    POLL_INTERVAL,
    PREREQ_TIMEOUT,
    PROVISION_TIMEOUT,
    poll,
)

pytestmark = pytest.mark.e2e

# transient states the provisioner passes through before settling
_TRANSIENT = {"BUILD", "STOPPING", "STARTING", "REBOOT", "DELETING"}

# CF1; the registered owner has a valid, authenticated session
def test_authenticated_session(client):
    r = client.get("/auth/me")
    assert r.status_code == 200, r.text
    me = r.json()
    assert me["role"] == "owner"
    assert "instance:delete" in me["permissions"]

# CF5; generate an SSH keypair and wait until Celery uploads it to OpenStack
def test_generate_keypair(client, ctx):
    r = client.post("/keypairs/generate", json={"name": "e2e-key", "key_type": "ed25519"})
    assert r.status_code == 201, r.text
    kp = r.json()
    assert kp["private_key"].startswith("-----BEGIN")  # returned exactly once
    ctx["keypair_id"] = kp["id"]

    poll(
        lambda: client.get("/keypairs/").json(),
        lambda ks: any(k["id"] == kp["id"] and k["openstack_name"] for k in ks),
        PREREQ_TIMEOUT, POLL_INTERVAL, "keypair upload to OpenStack",
    )


def test_provision_network(client, ctx):
    r = client.post(
        "/networks/",
        json={"name": "e2e-net", "subnets": [{"name": "e2e-subnet", "cidr": "10.99.0.0/24"}]},
    )
    assert r.status_code == 201, r.text
    net_id = r.json()["id"]
    ctx["network_id"] = net_id

    net = poll(
        lambda: next((n for n in client.get("/networks/").json() if n["id"] == net_id), None),
        lambda n: n and n["subnets"] and n["subnets"][0]["openstack_subnet_id"],
        PREREQ_TIMEOUT, POLL_INTERVAL, "subnet provisioning in OpenStack",
    )
    ctx["subnet_id"] = net["subnets"][0]["id"]


def test_create_security_group(client, ctx):
    r = client.post(
        "/security-groups/",
        json={
            "name": "e2e-sg",
            "description": "E2E SSH access",
            "rules": [{
                "direction": "ingress", "protocol": "tcp",
                "port_range_min": 22, "port_range_max": 22,
                "remote_ip_prefix": "0.0.0.0/0",
            }],
        },
    )
    assert r.status_code == 201, r.text
    sg = r.json()
    ctx["sg_id"] = sg["id"]

    poll(
        lambda: client.get("/security-groups/").json(),
        lambda gs: any(g["id"] == sg["id"] and g["openstack_id"] for g in gs),
        PREREQ_TIMEOUT, POLL_INTERVAL, "security group mirroring to OpenStack",
    )


def test_launch_instance(client, ctx):
    assert {"keypair_id", "subnet_id", "sg_id"} <= ctx.keys(), "prerequisites missing"

    payload = {
        "name": "e2e-vm",
        "flavor_name": FLAVOR,
        "image_name": IMAGE,
        "keypair_id": ctx["keypair_id"],
        "subnet_id": ctx["subnet_id"],
        "security_group_ids": [ctx["sg_id"]],
        "assign_floating_ip": ASSIGN_FIP,
    }

    r = client.post("/instances/", json=payload)
    assert r.status_code == 201, r.text

    body = r.json()
    assert isinstance(body, list) and len(body) == 1
    instance = body[0]
    assert instance["status"] == "BUILD"
    ctx["instance_id"] = instance["id"]

    detail = poll(
        lambda: client.get(f"/instances/{ctx['instance_id']}").json(),
        lambda d: d["status"] not in _TRANSIENT,
        PROVISION_TIMEOUT, POLL_INTERVAL, "instance to leave a transient state",
    )

    if detail["status"] != "ACTIVE":
        events = client.get(f"/instances/{ctx['instance_id']}/events").json()
        errors = [e["message"] for e in events if e["severity"] == "error"]
        reason = errors[-1] if errors else "(no error event — check the Celery worker log)"
        pytest.fail(f"instance settled in {detail['status']} instead of ACTIVE — {reason}")
    assert detail["private_ip_address"], "ACTIVE instance has no private IP"


def test_instance_detail_specs(client, ctx):
    r = client.get(f"/instances/{ctx['instance_id']}")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["vcpus"] >= 1 and d["ram_mb"] >= 1 and d["disk_gb"] >= 1
    assert d["openstack_id"]
    assert d["keypair"] and d["subnet"]


def test_power_cycle(client, ctx):
    iid = ctx["instance_id"]

    r = client.post(f"/instances/{iid}/stop")
    assert r.status_code == 200, r.text
    d = poll(
        lambda: client.get(f"/instances/{iid}").json(),
        lambda d: d["status"] not in _TRANSIENT,
        PROVISION_TIMEOUT, POLL_INTERVAL, "instance to stop",
    )
    assert d["status"] == "SHUTOFF", f"expected SHUTOFF, got {d['status']}"

    r = client.post(f"/instances/{iid}/start")
    assert r.status_code == 200, r.text
    d = poll(
        lambda: client.get(f"/instances/{iid}").json(),
        lambda d: d["status"] not in _TRANSIENT,
        PROVISION_TIMEOUT, POLL_INTERVAL, "instance to start",
    )
    assert d["status"] == "ACTIVE", f"expected ACTIVE, got {d['status']}"


def test_event_log(client, ctx):
    r = client.get(f"/instances/{ctx['instance_id']}/events")
    assert r.status_code == 200, r.text
    events = r.json()
    assert len(events) >= 1
    assert {"severity", "message", "created_at"} <= events[0].keys()


def test_delete_instance(client, ctx):
    iid = ctx["instance_id"]
    r = client.delete(f"/instances/{iid}")
    assert r.status_code == 200, r.text

    poll(
        lambda: client.get(f"/instances/{iid}").status_code,
        lambda code: code == 404,
        PROVISION_TIMEOUT, POLL_INTERVAL, "instance to be fully deleted",
    )
    # mark as handled so the ctx teardown does not try to delete it again
    ctx.pop("instance_id", None)
