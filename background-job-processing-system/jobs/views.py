from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Job, JOB_TYPE_CHOICES
from .serializers import JobSerializer, FileUploadJobSerializer
from .tasks import execute_job_task

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all().order_by('-created_at')
    def get_serializer_class(self):
        if self.action == 'upload_file':
            return FileUploadJobSerializer
        return JobSerializer

    def perform_create(self, serializer):
        job = serializer.save()
        execute_job_task.delay(job.id)

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
            execute_job_task.delay(job.id)
            return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Create your views here.
