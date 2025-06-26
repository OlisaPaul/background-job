from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from jobs.models import Job
import tempfile
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
import json

class JobApiTests(APITestCase):
    def test_create_immediate_email_job(self):
        url = reverse('job-list')
        data = {
            'job_type': 'send_email',
            'parameters': {
                'subject': 'Test',
                'body': 'Hello',
                'recipient': 'test@example.com'
            },
            'schedule_type': 'immediate'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['schedule_type'], 'immediate')
        self.assertIsNone(response.data['scheduled_time'])

    def test_create_scheduled_email_job(self):
        url = reverse('job-list')
        future_time = (timezone.now() + timezone.timedelta(hours=1)).isoformat()
        data = {
            'job_type': 'send_email',
            'parameters': {
                'subject': 'Test',
                'body': 'Hello',
                'recipient': 'test@example.com'
            },
            'schedule_type': 'scheduled',
            'scheduled_time': future_time
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['schedule_type'], 'scheduled')
        self.assertIsNotNone(response.data['scheduled_time'])

    def test_create_immediate_file_upload_job(self):
        url = reverse('job-upload-file')
        file_content = b'hello world' * 100
        file = SimpleUploadedFile('test.txt', file_content, content_type='text/plain')
        data = {
            'file': file,
            'schedule_type': 'immediate',
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['schedule_type'], 'immediate')
        self.assertIsNone(response.data['scheduled_time'])

    def test_create_scheduled_file_upload_job(self):
        url = reverse('job-upload-file')
        file_content = b'hello world' * 100
        file = SimpleUploadedFile('test.txt', file_content, content_type='text/plain')
        future_time = (timezone.now() + timezone.timedelta(hours=1)).isoformat()
        data = {
            'file': file,
            'schedule_type': 'scheduled',
            'scheduled_time': future_time
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['schedule_type'], 'scheduled')
        self.assertIsNotNone(response.data['scheduled_time'])

    def test_file_upload_too_large(self):
        url = reverse('job-upload-file')
        file_content = b'a' * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte
        file = SimpleUploadedFile('big.txt', file_content, content_type='text/plain')
        data = {
            'file': file,
            'schedule_type': 'immediate',
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)

    def test_scheduled_time_required_for_scheduled(self):
        url = reverse('job-list')
        data = {
            'job_type': 'send_email',
            'parameters': {
                'subject': 'Test',
                'body': 'Hello',
                'recipient': 'test@example.com'
            },
            'schedule_type': 'scheduled',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('scheduled_time', str(response.data))

    def test_scheduled_time_must_be_future(self):
        url = reverse('job-list')
        past_time = (timezone.now() - timezone.timedelta(hours=1)).isoformat()
        data = {
            'job_type': 'send_email',
            'parameters': {
                'subject': 'Test',
                'body': 'Hello',
                'recipient': 'test@example.com'
            },
            'schedule_type': 'scheduled',
            'scheduled_time': past_time
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('scheduled_time', str(response.data))
