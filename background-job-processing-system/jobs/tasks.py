from celery import shared_task
from .models import Job
import time
from django.core.mail import send_mail
from django.conf import settings
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import base64
import os
from django_celery_beat.models import PeriodicTask
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@shared_task(bind=True, max_retries=3)
def execute_job_task(self, job_id):
    job = Job.objects.get(id=job_id)
    job.status = 'running'
    job.save()
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
            result = {'message': f"Email sent to {params.get('recipient')}"}
        elif job.job_type == 'upload_file':
            params = job.parameters
            s3 = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION')
            )
            temp_path = params['temp_path']
            file_name = params['file_name']
            bucket = os.getenv('AWS_STORAGE_BUCKET_NAME')
            if not os.path.exists(temp_path):
                job.status = 'failed'
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
            # Remove the temp file after upload
            os.remove(temp_path)
        else:
            # Simulate other job processing
            time.sleep(2)
            result = {'message': f"{job.job_type} completed successfully."}
        job.status = 'completed'
        job.result = result
        # Notify websocket clients
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
    except Exception as exc:
        job.status = 'failed'
        job.retries += 1
        job.save()
        raise self.retry(exc=exc, countdown=2 ** job.retries)
    job.save()

@shared_task
def enable_periodic_task(periodic_task_id):
    try:
        pt = PeriodicTask.objects.get(id=periodic_task_id)
        pt.enabled = True
        pt.save()
    except PeriodicTask.DoesNotExist:
        pass
