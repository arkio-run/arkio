from celery import Celery

from ark.config import load_infra_config

app = Celery("tasks", broker=load_infra_config().celery_broker)
app.config_from_object("ark.celery.config")
