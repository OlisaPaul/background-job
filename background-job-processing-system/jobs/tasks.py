from celery import shared_task
from .models import Job
import time
from django.core.mail import send_mail
from django.conf import settings
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import base64
import os

@shared_task(bind=True, max_retries=3)
def execute_job_task(self, job_id):
    job = Job.objects.get(id=job_id)
    print(f"Executing job {job_id} of type {job.job_type} with parameters {job.parameters}")
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
    except Exception as exc:
        job.status = 'failed'
        job.retries += 1
        job.save()
        raise self.retry(exc=exc, countdown=2 ** job.retries)
    job.save()
