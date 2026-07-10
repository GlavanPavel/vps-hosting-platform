from fastapi import APIRouter, HTTPException
from core.influx import query_api
from core.config import config
from routers.deps import CurrentUserDep

metrics_router = APIRouter()

_RANGE_WINDOW = {
    "-30m": "1m",
    "-1h": "1m",
    "-24h": "15m",
    "-30d": "6h",
}


@metrics_router.get("/instances/{instance_id}/metrics")
def get_instance_metrics(instance_id: str, user_id: CurrentUserDep, time_range: str = "-1h"):
    window = _RANGE_WINDOW.get(time_range)
    if window is None:
        time_range, window = "-1h", "1m"

    flux_query = f'''
        from(bucket: "{config.INFLUXDB_BUCKET}")
        |> range(start: {time_range})
        |> filter(fn: (r) => r["_measurement"] == "server_metrics")
        |> filter(fn: (r) => r["instance_id"] == "{instance_id}")
        |> filter(fn: (r) => r["_field"] == "cpu_time" or r["_field"] == "ram_mb")
        |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> keep(columns: ["_time", "cpu_time", "ram_mb"])
    '''

    try:
        tables = query_api.query(org=config.INFLUXDB_ORG, query=flux_query)

        results = []
        for table in tables:
            for record in table.records:
                results.append({
                    "timestamp": record.get_time().isoformat(),
                    "cpu_time": record.values.get("cpu_time", 0.0),
                    "ram_mb": record.values.get("ram_mb", 0.0)
                })

        return {"instance_id": instance_id, "data": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare la citirea InfluxDB: {str(e)}")