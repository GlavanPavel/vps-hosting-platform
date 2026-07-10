import openstack
from core.celery_app import celery_app
from core.config import config
from core.influx import write_metric


@celery_app.task(name="collect_telemetry_data")
def poll_instance_metrics():
    conn = openstack.connect(
        auth_url=config.OS_AUTH_URL,
        project_name=config.OS_PROJECT_NAME,
        username=config.OS_USERNAME,
        password=config.OS_PASSWORD,
        user_domain_name=config.OS_USER_DOMAIN_NAME,
        project_domain_name=config.OS_PROJECT_DOMAIN_NAME,
    )

    servers = conn.compute.servers(status="ACTIVE")

    for server in servers:
        instance_id = server.id
        try:
            diagnostics = conn.compute.get_server_diagnostics(instance_id)

            ram_usage_mb = 0.0
            cpu_time = 0.0

            if hasattr(diagnostics, "memory_details") and diagnostics.memory_details:
                ram_usage_mb = float(diagnostics.memory_details.get("used", 0))

            if hasattr(diagnostics, "cpu_details") and diagnostics.cpu_details:
                for cpu in diagnostics.cpu_details:
                    cpu_time += float(cpu.get("time", 0))

            write_metric(instance_id, cpu_time, ram_usage_mb)

        except Exception as e:
            print(f"Could not collect metrics for {instance_id}: {e}")
