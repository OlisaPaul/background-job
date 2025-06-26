from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Job, JOB_TYPE_CHOICES
from .serializers import JobSerializer, FileUploadJobSerializer
from .tasks import execute_job_task
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
import json
from datetime import datetime
from django.utils import timezone

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'upload_file':
            return FileUploadJobSerializer
        return JobSerializer

    def handle_job_scheduling(self, job):
        if job.schedule_type == 'immediate' and not job.scheduled_time:
            execute_job_task.delay(job.id)
        elif job.schedule_type == 'immediate' and job.scheduled_time:
            execute_job_task.apply_async(args=[job.id], eta=job.scheduled_time)
        else:
            self.create_periodic_task(job)

    def perform_create(self, serializer):
        job = serializer.save()
        self.handle_job_scheduling(job)

    def create_periodic_task(self, job):
        PeriodicTask.objects.filter(name=f'job-{job.id}').delete()
        start = job.scheduled_time or timezone.now()
        minute = str(start.minute)
        hour = str(start.hour)
        day = str(start.day)
        month = str(start.month)
        enabled = True
        if job.scheduled_time and job.scheduled_time > timezone.now():
            enabled = False
        if job.schedule_type == 'hourly':
            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute=minute, hour='*', day_of_month='*', month_of_year='*', day_of_week='*'
            )
        elif job.schedule_type == 'daily':
            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute=minute, hour=hour, day_of_month='*', month_of_year='*', day_of_week='*'
            )
        elif job.schedule_type == 'monthly':
            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute=minute, hour=hour, day_of_month=day, month_of_year='*', day_of_week='*'
            )
        elif job.schedule_type == 'yearly':
            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute=minute, hour=hour, day_of_month=day, month_of_year=month, day_of_week='*'
            )
        else:
            return
        pt = PeriodicTask.objects.create(
            crontab=schedule,
            name=f'job-{job.id}',
            task='jobs.tasks.execute_job_task',
            args=json.dumps([job.id]),
            start_time=start,
            enabled=enabled
        )
        if not enabled:
            from django_celery_beat.models import ClockedSchedule
            clocked, _ = ClockedSchedule.objects.get_or_create(clocked_time=start)
            PeriodicTask.objects.create(
                clocked=clocked,
                one_off=True,
                name=f'enable-job-{job.id}',
                task='jobs.tasks.enable_periodic_task',
                args=json.dumps([pt.id]),
                enabled=True
            )

    @action(detail=False, methods=['get'])
    def types(self, request):
        return Response([{'key': k, 'label': v} for k, v in JOB_TYPE_CHOICES])

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        job = self.get_object()
        if job.status != 'failed':
            return Response({'error': 'Only failed jobs can be retried.'}, status=status.HTTP_400_BAD_REQUEST)
        job.status = 'pending'
        job.retries = 0
        job.save()
        execute_job_task.delay(job.id)
        return Response({'status': 'Job retried.'})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        return Response({
            'total': Job.objects.count(),
            'pending': Job.objects.filter(status='pending').count(),
            'running': Job.objects.filter(status='running').count(),
            'completed': Job.objects.filter(status='completed').count(),
            'failed': Job.objects.filter(status='failed').count(),
        })

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser], url_path='upload-file')
    def upload_file(self, request):
        serializer = FileUploadJobSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save()
            self.handle_job_scheduling(job)
            return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Create your views here.
