from django.utils import timezone
from django_celery_beat.models import ClockedSchedule, PeriodicTask
import json

run_time = timezone.now() + timezone.timedelta(minutes=2)
clocked, _ = ClockedSchedule.objects.get_or_create(clocked_time=run_time)

PeriodicTask.objects.create(
    name='test-enable-task',
    clocked=clocked,
    one_off=True,
    task='jobs.tasks.enable_periodic_task',  # or 'jobs.tasks.execute_job_task' if you want to test that directly
    args=json.dumps([1]),  # use a real task or dummy job ID
    enabled=True,
)