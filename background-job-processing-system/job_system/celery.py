import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_system.settings')

app = Celery('job_system')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'send-mail-every-day-at-1': {
        'task': 'playground.tasks.notify_customers',
        'schedule': crontab(hour=14, minute=4),
        'args': ('Hello World',),
    }
}


app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')