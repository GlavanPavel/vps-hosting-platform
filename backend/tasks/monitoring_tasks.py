from core.celery_app import celery_app
from models.instance import Instance
from models.instance_event import InstanceEvent
from models.cloud_stats import CloudStats
from tasks.common import SessionLocal, _os_connect


_TRANSIENT_STATES = {"BUILD", "DELETING", "STOPPING", "STARTING", "REBOOT"}


@celery_app.task(name="sync_instance_states")
def sync_instance_states():
    conn = _os_connect()
    os_status = {s.id: s.status for s in conn.compute.servers()}
    updated = 0
    with SessionLocal() as db:
        instances = db.query(Instance).filter(Instance.openstack_id.isnot(None)).all()
        for inst in instances:
            if inst.status in _TRANSIENT_STATES:
                continue
            # a server missing from OpenStack but still in our DB → flag ERROR
            live = os_status.get(inst.openstack_id, "ERROR")
            if live != inst.status:
                if live == "ERROR":
                    db.add(InstanceEvent(
                        instance_id=inst.id, severity="error",
                        message="Instance entered ERROR (detected by health check)",
                    ))
                elif live == "SHUTOFF":
                    db.add(InstanceEvent(
                        instance_id=inst.id, severity="warning",
                        message="Instance powered off outside the dashboard",
                    ))
                elif live == "ACTIVE":
                    db.add(InstanceEvent(
                        instance_id=inst.id, severity="info",
                        message="Instance is active again",
                    ))
                inst.status = live
                updated += 1
        if updated:
            db.commit()
    return {"checked": len(os_status), "updated": updated}


_METER_INTERVAL_SECONDS = 60


@celery_app.task(name="meter_usage")
def meter_usage():
    with SessionLocal() as db:
        metered = (
            db.query(Instance)
            .filter(Instance.status == "ACTIVE")
            .update(
                {Instance.running_seconds: Instance.running_seconds + _METER_INTERVAL_SECONDS},
                synchronize_session=False,
            )
        )
        db.commit()
    return {"metered": metered}


def _num(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


@celery_app.task(name="collect_cloud_stats")
def collect_cloud_stats():
    try:
        conn = _os_connect()
    except Exception as exc:
        print(f"[collect_cloud_stats] connect failed: {exc}")
        return {"status": "error", "error": str(exc)}

    hcount = vcpus_total = vcpus_used = ram_total = ram_used = 0
    disk_total = disk_used = running = 0
    try:
        resp = conn.compute.get("/os-hypervisors/statistics", microversion="2.87")
        resp.raise_for_status()
        s = resp.json().get("hypervisor_statistics", {})
        hcount = int(s.get("count", 0) or 0)
        vcpus_total = int(s.get("vcpus", 0) or 0)
        vcpus_used = int(s.get("vcpus_used", 0) or 0)
        ram_total = int(s.get("memory_mb", 0) or 0)
        ram_used = int(s.get("memory_mb_used", 0) or 0)
        disk_total = int(s.get("local_gb", 0) or 0)
        disk_used = int(s.get("local_gb_used", 0) or 0)
        running = int(s.get("running_vms", 0) or 0)
    except Exception as exc:
        print(f"[collect_cloud_stats] statistics endpoint failed ({exc}); trying hypervisor list")
        try:
            for h in conn.compute.hypervisors(details=True):
                hcount += 1
                vcpus_total += int(getattr(h, "vcpus", 0) or 0)
                vcpus_used += int(getattr(h, "vcpus_used", 0) or 0)
                ram_total += int(getattr(h, "memory_size", None) or getattr(h, "memory_mb", 0) or 0)
                ram_used += int(getattr(h, "memory_used", None) or getattr(h, "memory_mb_used", 0) or 0)
                disk_total += int(getattr(h, "local_disk_size", None) or getattr(h, "local_gb", 0) or 0)
                disk_used += int(getattr(h, "local_disk_used", None) or getattr(h, "local_gb_used", 0) or 0)
                running += int(getattr(h, "running_vms", 0) or 0)
        except Exception as exc2:
            print(f"[collect_cloud_stats] hypervisor list also failed: {exc2}")

    storage_total = storage_used = None
    try:
        total = free = 0.0
        for pool in conn.block_storage.backend_pools():
            caps = getattr(pool, "capabilities", {}) or {}
            total += _num(caps.get("total_capacity_gb"))
            free += _num(caps.get("free_capacity_gb"))
        if total > 0:
            storage_total = int(total)
            storage_used = int(total - free)
    except Exception as exc:
        print(f"[collect_cloud_stats] cinder capacity unavailable: {exc}")

    with SessionLocal() as db:
        row = db.query(CloudStats).order_by(CloudStats.id.desc()).first()
        if not row:
            row = CloudStats()
            db.add(row)
        row.hypervisor_count = hcount
        row.vcpus_total = vcpus_total
        row.vcpus_used = vcpus_used
        row.ram_mb_total = ram_total
        row.ram_mb_used = ram_used
        row.disk_gb_total = disk_total
        row.disk_gb_used = disk_used
        row.running_vms = running
        row.storage_gb_total = storage_total
        row.storage_gb_used = storage_used
        db.commit()

    print(f"[collect_cloud_stats] {hcount} hypervisor(s): {vcpus_used}/{vcpus_total} vCPU, "
          f"{ram_used}/{ram_total} MB RAM")
    return {"status": "success", "hypervisors": hcount}
