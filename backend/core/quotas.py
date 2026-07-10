DEFAULT_QUOTA: dict[str, int] = {
    "max_instances": 10,
    "max_vcpus": 20,
    "max_ram_gb": 48,
    "max_volumes": 20,
    "max_storage_gb": 500,
    "max_floating_ips": 5,
}

# the limit columns, in order
QUOTA_FIELDS: list[str] = list(DEFAULT_QUOTA.keys())
