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

    def test_job_list_pagination_integration(self):
        url = reverse('job-list')
        # Create 23 jobs
        for i in range(23):
            Job.objects.create(
                job_type='send_email',
                parameters={"recipient": f"user{i}@example.com", "subject": "s", "body": "b"},
                schedule_type='immediate',
            )
        # First page
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['count'], 23)
        # Third page
        response = self.client.get(url + '?page=3')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        # Out-of-range page
        response = self.client.get(url + '?page=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    @patch('jobs.tasks.execute_job_task.delay')
    def test_immediate_email_job_triggers_celery_via_dedicated_endpoint(self, mock_celery_delay):
        url = reverse('job-send-email')
        data = {
            'recipient': 'integration@example.com',
            'subject': 'Integration',
            'body': 'Integration test',
            'schedule_type': 'immediate'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        job = Job.objects.get(id=response.data['id'])
        self.assertEqual(job.status, 'pending')
        mock_celery_delay.assert_called_once_with(job.id)

    @patch('jobs.tasks.execute_job_task.delay')
    def test_immediate_file_upload_job_creates_file_and_job_via_dedicated_endpoint(self, mock_celery_delay):
        url = reverse('job-upload-file-standalone')
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

    @patch('jobs.tasks.execute_job_task.delay')
    def test_personalized_bulk_email_jobs_trigger_celery(self, mock_celery_delay):
        url = reverse('job-send-email')
        data = {
            'emails': [
                {'recipient': 'a@example.com', 'subject': 'A', 'body': 'Hello A'},
                {'recipient': 'b@example.com', 'subject': 'B', 'body': 'Hello B'},
            ],
            'schedule_type': 'immediate'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 2)
        jobs = Job.objects.filter(parameters__recipient__in=['a@example.com', 'b@example.com'])
        self.assertEqual(jobs.count(), 2)
        # Should trigger celery for each job
        self.assertEqual(mock_celery_delay.call_count, 2)
        called_ids = {call.args[0] for call in mock_celery_delay.call_args_list}
        self.assertEqual(set(jobs.values_list('id', flat=True)), called_ids)
