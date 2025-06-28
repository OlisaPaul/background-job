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

    def test_job_list_pagination_default(self):
        url = reverse('job-list')
        # Create 15 jobs
        for i in range(15):
            Job.objects.create(
                job_type='send_email',
                parameters={"recipient": f"user{i}@example.com", "subject": "s", "body": "b"},
                schedule_type='immediate',
            )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['count'], 15)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

    def test_job_list_pagination_second_page(self):
        url = reverse('job-list')
        for i in range(15):
            Job.objects.create(
                job_type='send_email',
                parameters={"recipient": f"user{i}@example.com", "subject": "s", "body": "b"},
                schedule_type='immediate',
            )
        response = self.client.get(url + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['count'], 15)
        self.assertIsNotNone(response.data['previous'])

    def test_job_list_pagination_invalid_page(self):
        url = reverse('job-list')
        response = self.client.get(url + '?page=999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # self.assertEqual(response.data['results'], [])  # Not needed, 404 means no results

    def test_job_list_pagination_non_integer_page(self):
        url = reverse('job-list')
        response = self.client.get(url + '?page=abc')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_job_list_filter_by_job_type(self):
        url = reverse('job-list')
        Job.objects.create(job_type='send_email', parameters={"recipient": "a@a.com", "subject": "s", "body": "b"}, schedule_type='immediate')
        Job.objects.create(job_type='upload_file', parameters={"file_name": "f", "temp_path": "t"}, schedule_type='immediate')
        response = self.client.get(url + '?job_type=send_email')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(j['job_type'] == 'send_email' for j in response.data['results']))

    def test_job_list_filter_by_status(self):
        url = reverse('job-list')
        Job.objects.create(job_type='send_email', parameters={"recipient": "a@a.com", "subject": "s", "body": "b"}, status='completed', schedule_type='immediate')
        Job.objects.create(job_type='send_email', parameters={"recipient": "b@b.com", "subject": "s", "body": "b"}, status='failed', schedule_type='immediate')
        response = self.client.get(url + '?status=completed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(j['status'] == 'completed' for j in response.data['results']))

    def test_job_list_filter_by_job_type_and_status(self):
        url = reverse('job-list')
        Job.objects.create(job_type='send_email', parameters={"recipient": "a@a.com", "subject": "s", "body": "b"}, status='completed', schedule_type='immediate')
        Job.objects.create(job_type='upload_file', parameters={"file_name": "f", "temp_path": "t"}, status='completed', schedule_type='immediate')
        Job.objects.create(job_type='send_email', parameters={"recipient": "b@b.com", "subject": "s", "body": "b"}, status='failed', schedule_type='immediate')
        response = self.client.get(url + '?job_type=send_email&status=completed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(j['job_type'] == 'send_email' and j['status'] == 'completed' for j in response.data['results']))

    def test_create_immediate_email_job_via_dedicated_endpoint(self):
        url = reverse('job-send-email')
        data = {
            'recipient': 'test@example.com',
            'subject': 'Test',
            'body': 'Hello',
            'schedule_type': 'immediate'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['schedule_type'], 'immediate')
        self.assertIsNone(response.data['scheduled_time'])
        self.assertEqual(response.data['job_type'], 'send_email')

    def test_create_scheduled_email_job_via_dedicated_endpoint(self):
        url = reverse('job-send-email')
        future_time = (timezone.now() + timezone.timedelta(hours=1)).isoformat()
        data = {
            'recipient': 'test@example.com',
            'subject': 'Test',
            'body': 'Hello',
            'schedule_type': 'scheduled',
            'scheduled_time': future_time
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['schedule_type'], 'scheduled')
        self.assertIsNotNone(response.data['scheduled_time'])
        self.assertEqual(response.data['job_type'], 'send_email')

    def test_create_immediate_file_upload_job_via_dedicated_endpoint(self):
        url = reverse('job-upload-file-standalone')
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
        self.assertEqual(response.data['job_type'], 'upload_file')

    def test_create_scheduled_file_upload_job_via_dedicated_endpoint(self):
        url = reverse('job-upload-file-standalone')
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
        self.assertEqual(response.data['job_type'], 'upload_file')

    def test_create_personalized_bulk_email_jobs(self):
        url = reverse('job-send-email')
        data = {
            'emails': [
                {'recipient': 'a@example.com', 'subject': 'A', 'body': 'Hello A'},
                {'recipient': 'b@example.com', 'subject': 'B', 'body': 'Hello B'},
                {'recipient': 'c@example.com', 'subject': 'C', 'body': 'Hello C'},
            ],
            'schedule_type': 'immediate'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 3)
        for i, email in enumerate(['a@example.com', 'b@example.com', 'c@example.com']):
            self.assertEqual(response.data[i]['parameters']['recipient'], email)
            self.assertEqual(response.data[i]['job_type'], 'send_email')
            self.assertEqual(response.data[i]['schedule_type'], 'immediate')

    def test_emails_bulk_email_validation(self):
        url = reverse('job-send-email')
        # Empty list
        data = {'emails': [], 'schedule_type': 'immediate'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Missing subject/body in one item
        data = {
            'emails': [
                {'recipient': 'a@example.com', 'subject': 'A', 'body': 'Hello'},
                {'recipient': 'b@example.com', 'subject': 'B'},  # missing body
            ],
            'schedule_type': 'immediate'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Providing multiple modes
        data = {
            'recipient': 'a@example.com',
            'emails': [
                {'recipient': 'b@example.com', 'subject': 'B', 'body': 'Hello'},
            ],
            'subject': 'S',
            'body': 'B',
            'schedule_type': 'immediate'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
