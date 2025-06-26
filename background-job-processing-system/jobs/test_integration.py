from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from jobs.models import Job
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
import os

class JobIntegrationTests(APITestCase):
    @patch('jobs.tasks.execute_job_task.delay')
    def test_immediate_email_job_triggers_celery(self, mock_celery_delay):
        url = reverse('job-list')
        data = {
            'job_type': 'send_email',
            'parameters': {
                'subject': 'Integration',
                'body': 'Integration test',
                'recipient': 'integration@example.com'
            },
            'schedule_type': 'immediate'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        job = Job.objects.get(id=response.data['id'])
        self.assertEqual(job.status, 'pending')
        mock_celery_delay.assert_called_once_with(job.id)

    def test_job_appears_in_db_after_creation(self):
        url = reverse('job-list')
        data = {
            'job_type': 'send_email',
            'parameters': {
                'subject': 'DB',
                'body': 'Check DB',
                'recipient': 'db@example.com'
            },
            'schedule_type': 'immediate'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Job.objects.filter(id=response.data['id']).exists())

    @patch('jobs.tasks.execute_job_task.delay')
    def test_immediate_file_upload_job_creates_file_and_job(self, mock_celery_delay):
        url = reverse('job-upload-file')
        file_content = b'integration test file'
        file = SimpleUploadedFile('integration.txt', file_content, content_type='text/plain')
        data = {
            'file': file,
            'schedule_type': 'immediate',
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        job_id = response.data['id']
        job = Job.objects.get(id=job_id)
        self.assertEqual(job.status, 'pending')
        params = job.parameters
        self.assertTrue(os.path.exists(params['temp_path']))
        mock_celery_delay.assert_called_once_with(job.id)
        # Clean up temp file
        os.remove(params['temp_path'])

    def test_scheduled_job_does_not_trigger_celery_immediately(self):
        url = reverse('job-list')
        future_time = (timezone.now() + timezone.timedelta(hours=2)).isoformat()
        data = {
            'job_type': 'send_email',
            'parameters': {
                'subject': 'Scheduled',
                'body': 'Should not run now',
                'recipient': 'future@example.com'
            },
            'schedule_type': 'scheduled',
            'scheduled_time': future_time
        }
        with patch('jobs.tasks.execute_job_task.delay') as mock_celery_delay:
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            mock_celery_delay.assert_not_called()
        job = Job.objects.get(id=response.data['id'])
        self.assertEqual(job.schedule_type, 'scheduled')
        self.assertEqual(job.scheduled_time.isoformat(), response.data['scheduled_time'].replace('Z', '+00:00'))
