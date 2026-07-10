FLAVOR_SPECS: dict[str, dict[str, int]] = {
    "m1.tiny": {"vcpu": 1, "ram_mb": 512, "disk_gb": 1},
    "m1.small": {"vcpu": 1, "ram_mb": 2048, "disk_gb": 20},
    "m1.medium": {"vcpu": 2, "ram_mb": 4096, "disk_gb": 40},
    "m1.large": {"vcpu": 4, "ram_mb": 8192, "disk_gb": 80},
    "m1.xlarge": {"vcpu": 8, "ram_mb": 16384, "disk_gb": 160},
    "m2.tiny": {"vcpu": 2, "ram_mb": 512, "disk_gb": 10},
}
DEFAULT_SPEC = {"vcpu": 1, "ram_mb": 512, "disk_gb": 1}


def flavor_spec(flavor_name: str) -> dict[str, int]:
    return FLAVOR_SPECS.get(flavor_name, DEFAULT_SPEC)
