import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from core.config import config

client = InfluxDBClient(
    url=config.INFLUXDB_URL,
    token=config.INFLUXDB_ADMIN_TOKEN,
    org=config.INFLUXDB_ORG
)
write_api = client.write_api(write_options=SYNCHRONOUS)

query_api = client.query_api()

def write_metric(instance_id: str, cpu_time: float, ram_usage_mb: float):
    point = (
        Point("server_metrics")
        .tag("instance_id", instance_id)
        .field("cpu_time", cpu_time)
        .field("ram_mb", ram_usage_mb)
    )
    write_api.write(bucket=config.INFLUXDB_BUCKET, org=config.INFLUXDB_ORG, record=point)