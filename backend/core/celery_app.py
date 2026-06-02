from celery import Celery

celery_app = Celery(
    "vps_tasks",
    broker="amqp://guest:guest@localhost:5672//",
    include=['tasks.vm_tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Bucharest',
    enable_utc=True,
)