from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Job, JOB_TYPE_CHOICES
from .serializers import JobSerializer, FileUploadJobSerializer, SendEmailJobSerializer
from .tasks import execute_job_task
from django_celery_beat.models import PeriodicTask, CrontabSchedule, ClockedSchedule
from django.utils import timezone
from django.views.generic import TemplateView
import boto3
import os
import json
from datetime import datetime

# --- Constants ---
JOB_STATUS_FAILED = 'failed'
JOB_STATUS_PENDING = 'pending'
JOB_STATUS_RUNNING = 'running'
JOB_STATUS_COMPLETED = 'completed'

class JobViewSet(viewsets.ModelViewSet):
    """ViewSet for managing background jobs."""
    queryset = Job.objects.all().order_by('-created_at')
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'priority', 'status']

    def get_serializer_class(self):
        """Return the appropriate serializer class based on the action."""
        if self.action == 'upload_file':
            return FileUploadJobSerializer
        elif self.action == 'send_email':
            return SendEmailJobSerializer
        return JobSerializer

    def handle_job_scheduling(self, job):
        """Schedule the job for execution based on its schedule_type."""
        if job.schedule_type == 'immediate':
            execute_job_task.delay(job.id)
        elif job.schedule_type == 'scheduled':
            execute_job_task.apply_async(args=[job.id], eta=job.scheduled_time)
        else:
            self.create_periodic_task(job)

    def perform_create(self, serializer):
        """Override to handle job scheduling after creation."""
        job = serializer.save()
        self.handle_job_scheduling(job)

    def get_queryset(self):
        """Optionally filter jobs by job_type and status."""
        queryset = super().get_queryset()
        job_type = self.request.query_params.get('job_type')
        status_param = self.request.query_params.get('status')
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def create_periodic_task(self, job):
        """Create a periodic or clocked task for recurring jobs."""
        # Remove any previous task with this job ID
        PeriodicTask.objects.filter(name=f'job-{job.id}').delete()
        PeriodicTask.objects.filter(name=f'enable-job-{job.id}').delete()

        start = job.scheduled_time or timezone.now()
        enabled = not (job.scheduled_time and job.scheduled_time > timezone.now())

        def get_crontab_schedule(job, start):
            minute = str(start.minute)
            hour = str(start.hour)
            day = str(start.day)
            month = str(start.month)
            schedule_map = {
                'hourly': dict(minute=minute, hour='*', day_of_month='*', month_of_year='*', day_of_week='*'),
                'daily': dict(minute=minute, hour=hour, day_of_month='*', month_of_year='*', day_of_week='*'),
                'monthly': dict(minute=minute, hour=hour, day_of_month=day, month_of_year='*', day_of_week='*'),
                'yearly': dict(minute=minute, hour=hour, day_of_month=day, month_of_year=month, day_of_week='*'),
            }
            schedule_params = schedule_map.get(job.frequency)
            if not schedule_params:
                raise ValueError(f"Unsupported schedule type: {job.frequency}")
            return CrontabSchedule.objects.get_or_create(**schedule_params)[0]

        schedule = get_crontab_schedule(job, start)
        periodic_task = PeriodicTask.objects.create(
            crontab=schedule,
            name=f'job-{job.id}',
            task='jobs.tasks.execute_job_task',
            args=json.dumps([job.id]),
            start_time=start,
            enabled=True
        )
        if not enabled:
            clocked = ClockedSchedule.objects.get_or_create(clocked_time=start)[0]
            PeriodicTask.objects.create(
                clocked=clocked,
                one_off=True,
                name=f'enable-job-{job.id}',
                task='jobs.tasks.enable_periodic_task',
                args=json.dumps([periodic_task.id]),
                enabled=True
            )

    @action(detail=False, methods=['get'])
    def types(self, request):
        """Return available job types."""
        return Response([{'key': k, 'label': v} for k, v in JOB_TYPE_CHOICES])

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed job."""
        job = self.get_object()
        if job.status != JOB_STATUS_FAILED:
            return Response({'error': 'Only failed jobs can be retried.'}, status=status.HTTP_400_BAD_REQUEST)
        job.status = JOB_STATUS_PENDING
        job.retries = 0
        job.save()
        execute_job_task.delay(job.id)
        return Response({'status': 'Job retried.'})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Return job statistics by status."""
        return Response({
            'total': Job.objects.count(),
            JOB_STATUS_PENDING: Job.objects.filter(status=JOB_STATUS_PENDING).count(),
            JOB_STATUS_RUNNING: Job.objects.filter(status=JOB_STATUS_RUNNING).count(),
            JOB_STATUS_COMPLETED: Job.objects.filter(status=JOB_STATUS_COMPLETED).count(),
            JOB_STATUS_FAILED: Job.objects.filter(status=JOB_STATUS_FAILED).count(),
        })

    @action(detail=False, methods=['post'], url_path='send-email')
    def send_email(self, request):
        """Create one or more email jobs (single, bulk, or personalized)."""
        serializer = SendEmailJobSerializer(data=request.data)
        if serializer.is_valid():
            jobs = serializer.save()
            if isinstance(jobs, list):
                for job in jobs:
                    self.handle_job_scheduling(job)
                return Response([JobSerializer(job).data for job in jobs], status=status.HTTP_201_CREATED)
            else:
                self.handle_job_scheduling(jobs)
                return Response(JobSerializer(jobs).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser], url_path='upload-file-standalone')
    def upload_file_standalone(self, request):
        """Create a file upload job (standalone endpoint)."""
        serializer = FileUploadJobSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save()
            self.handle_job_scheduling(job)
            return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser], url_path='upload-file')
    def upload_file(self, request):
        """Create a file upload job (main endpoint)."""
        serializer = FileUploadJobSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save()
            self.handle_job_scheduling(job)
            return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _get_s3_client(self):
        """Helper to create an S3 client using environment variables."""
        return boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )

    @action(detail=True, methods=['get'], url_path='download-url')
    def download_url(self, request, pk=None):
        """Generate a presigned S3 download URL for a file upload job."""
        job = self.get_object()
        if job.job_type != 'upload_file' or not job.result or not isinstance(job.result, dict):
            return Response({'error': 'No downloadable file for this job.'}, status=status.HTTP_400_BAD_REQUEST)
        file_url = job.result.get('file_url')
        file_name = file_url.split('/')[-1] if file_url else job.parameters.get('file_name')
        if not file_name:
            return Response({'error': 'File name not found.'}, status=status.HTTP_400_BAD_REQUEST)
        s3 = self._get_s3_client()
        bucket = os.getenv('AWS_STORAGE_BUCKET_NAME')
        try:
            presigned_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': file_name},
                ExpiresIn=3600
            )
            return Response({'download_url': presigned_url})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- WebSocket Test View ---
class TestWebSocketView(TemplateView):
    """Simple template for testing WebSocket permissions."""
    template_name = 'websocket_permissions.html'
