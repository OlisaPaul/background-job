from celery import shared_task
from .models import Job, JOB_STATUS_FAILED, JOB_STATUS_PENDING, JOB_STATUS_COMPLETED
import time
from django.core.mail import send_mail
from django.conf import settings
import boto3
import os
from django_celery_beat.models import PeriodicTask
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@shared_task(bind=True, max_retries=3)
def execute_job_task(self, job_id):
    """
    Celery task to execute a background job by ID.
    Handles email, file upload, and generic jobs. Updates job status and notifies WebSocket clients.
    """
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        # Job was deleted before execution; send websocket update and exit
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'job_status',
            {
                'type': 'job_status_update',
                'data': {
                    'id': job_id,
                    'status': 'deleted',
                    'result': {'error': 'Job was deleted before execution.'},
                }
            }
        )
        print(f"WebSocket update sent for deleted job {job_id}")
        return
    job.status = 'running'
    job.save()
    # Send websocket update for running status
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'job_status',
        {
            'type': 'job_status_update',
            'data': {
                'id': job.id,
                'status': job.status,
                'result': job.result,
            }
        }
    )
    try:
        result = None
        if job.job_type == 'send_email':
            params = job.parameters
            send_mail(
                subject=params.get('subject', ''),
                message=params.get('body', ''),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
                recipient_list=[params.get('recipient')],
                fail_silently=False,
            )
            result = {'message': f"Email sent to {params.get('recipient')}", 'recipient': params.get('recipient')}
        elif job.job_type == 'upload_file':
            params = job.parameters
            s3 = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            temp_path = params['temp_path']
            file_name = params['file_name']
            bucket = os.getenv('AWS_STORAGE_BUCKET_NAME')
            if not os.path.exists(temp_path):
                job.status = JOB_STATUS_FAILED
                job.result = {'error': f"File {file_name} not found at {temp_path}. It may have been deleted before the scheduled job ran."}
                job.save()
                return
            with open(temp_path, 'rb') as f:
                s3.put_object(Bucket=bucket, Key=file_name, Body=f)
            region = os.getenv('AWS_REGION', 'us-east-1')
            file_url = f"https://{bucket}.s3.{region}.amazonaws.com/{file_name}"
            result = {
                'message': f"File {file_name} uploaded to S3.",
                'file_url': file_url
            }
            os.remove(temp_path)
        else:
            # Simulate other job processing
            time.sleep(2)
            result = {'message': f"{job.job_type} completed successfully."}
        job.status = JOB_STATUS_COMPLETED
        job.result = result
        # Notify websocket clients
        async_to_sync(channel_layer.group_send)(
            'job_status',
            {
                'type': 'job_status_update',
                'data': {
                    'id': job.id,
                    'status': job.status,
                    'result': job.result,
                }
            }
        )
        print(f"WebSocket update sent for job {job.id} with status {job.status}")
    except Exception as exc:
        job.status = JOB_STATUS_FAILED
        job.retries += 1
        job.save()
        raise self.retry(exc=exc, countdown=2 ** job.retries)
    job.save()

@shared_task
def enable_periodic_task(periodic_task_id):
    """
    Celery task to enable a periodic task by ID (used for scheduled jobs).
    """
    try:
        pt = PeriodicTask.objects.get(id=periodic_task_id)
        pt.enabled = True
        pt.save()
        print(f"[✓] Periodic task '{pt.name}' (ID: {periodic_task_id}) has been enabled.")
    except PeriodicTask.DoesNotExist:
        print(f"[✗] Periodic task with ID {periodic_task_id} not found.")
