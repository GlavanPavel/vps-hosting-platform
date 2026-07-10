"""Celery task package, split by resource. Importing this package registers every
@on(...) handler with the domain dispatcher — FastAPI does `import tasks` for exactly
that reason, and the Celery worker imports it via the `include` list in
core/celery_app.py. The unit-test suite deliberately never imports it, which keeps
the dispatcher a no-op there."""
from tasks import (
    instance_tasks,
    keypair_tasks,
    security_group_tasks,
    network_tasks,
    floating_ip_tasks,
    volume_tasks,
    image_tasks,
    monitoring_tasks,
    org_tasks,
    telemetry,
)
