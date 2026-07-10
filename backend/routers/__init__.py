from routers.instances import instance_router
from routers.metrics import metrics_router
from routers.keypairs import keypair_router
from routers.security_groups import security_group_router
from routers.networks import network_router
from routers.floating_ips import floating_ip_router
from routers.volumes import volume_router
from routers.images import image_router
from routers.org import org_router
from routers.usage import usage_router
from routers.quotas import quota_router
from routers.admin import admin_router
from routers.auth import auth_router

__all__ = [
    "auth_router",
    "instance_router",
    "metrics_router",
    "keypair_router",
    "security_group_router",
    "network_router",
    "floating_ip_router",
    "volume_router",
    "image_router",
    "org_router",
    "usage_router",
    "quota_router",
    "admin_router",
]
