from celery import Celery

celery_app = Celery(
    "vps_tasks",
    broker="amqp://guest:guest@localhost:5672//",
    # rpc backend returns task results over RabbitMQ
    backend="rpc://",
    # imports all tasks
    include=['tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Bucharest',
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    'colecteaza-metrice-la-fiecare-60s': {
        'task': 'collect_telemetry_data',
        'schedule': 60.0,
    },
    # periodic health check
    'sync-instance-states-30s': {
        'task': 'sync_instance_states',
        'schedule': 30.0,
    },
    # usage metering
    'meter-usage-60s': {
        'task': 'meter_usage',
        'schedule': 60.0,
    },
    # admin dashboard
    'collect-cloud-stats-60s': {
        'task': 'collect_cloud_stats',
        'schedule': 60.0,
    },
}

celery_app.conf.timezone = 'Europe/Bucharest'