from celery import Celery

celery_app = Celery(
    "vps_tasks",
    broker="amqp://guest:guest@localhost:5672//",
    include=['tasks.vm_tasks', 'tasks.telemetry']
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
}

celery_app.conf.timezone = 'Europe/Bucharest'