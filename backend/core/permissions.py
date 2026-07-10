# every gated action in the system
ALL_PERMISSIONS: set[str] = {
    "instance:create", "instance:delete", "instance:power", "instance:snapshot",
    "volume:create", "volume:delete", "volume:attach",
    "network:create", "network:delete",
    "security_group:create", "security_group:delete",
    "floating_ip:manage", "floating_ip:release",
    "keypair:manage",
    "image:create", "image:delete", "image:publish",
    "org:manage",
}

# actions reserved for owners
OWNER_ONLY: set[str] = {
    "instance:delete",
    "volume:delete",
    "network:delete",
    "security_group:delete",
    "floating_ip:release",
    "image:delete",
    "image:publish",
    "org:manage",
}

# superuser capability
ADMIN_VIEW = "admin:view"

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner": set(ALL_PERMISSIONS),
    "member": ALL_PERMISSIONS - OWNER_ONLY,
    "admin": set(ALL_PERMISSIONS) | {ADMIN_VIEW},
}


def permissions_for(role: str) -> set[str]:
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: str, permission: str) -> bool:
    return permission in permissions_for(role)
