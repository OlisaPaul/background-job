from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from jobs.models import Job
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from django_celery_beat.models import PeriodicTask

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
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['count'], 23)
        # Third page
        response = self.client.get(url + '?page=3')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        # Fifth page
        response = self.client.get(url + '?page=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        # Out-of-range page
        response = self.client.get(url + '?page=6')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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

    def test_deleting_scheduled_job_removes_periodic_task(self):
        """Deleting a scheduled job also deletes its associated PeriodicTask."""
        url = reverse('job-list')
        future_time = (timezone.now() + timezone.timedelta(hours=1)).isoformat()
        data = {
            'job_type': 'send_email',
            'parameters': {
                'subject': 'Scheduled',
                'body': 'Should be scheduled',
                'recipient': 'future@example.com'
            },
            'schedule_type': 'scheduled',
            'scheduled_time': future_time
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        job_id = response.data['id']
        # Simulate periodic task creation (if not auto-created)
        job = Job.objects.get(id=job_id)
        from jobs.views import JobViewSet
        viewset = JobViewSet()
        viewset.create_periodic_task(job)
        # Check that the periodic task exists
        self.assertTrue(PeriodicTask.objects.filter(name=f'job-{job_id}').exists())
        # Delete the job
        del_url = reverse('job-detail', args=[job_id])
        del_response = self.client.delete(del_url)
        self.assertEqual(del_response.status_code, status.HTTP_204_NO_CONTENT)
        # Check that the periodic task is deleted
        self.assertFalse(PeriodicTask.objects.filter(name=f'job-{job_id}').exists())

    def test_deleting_periodic_job_removes_all_related_tasks(self):
        """Deleting a periodic job removes all related PeriodicTasks (including enable-job-*)."""
        url = reverse('job-list')
        future_time = (timezone.now() + timezone.timedelta(hours=1)).isoformat()
        data = {
            'job_type': 'send_email',
            'parameters': {
                'subject': 'Periodic',
                'body': 'Should be periodic',
                'recipient': 'periodic@example.com'
            },
            'schedule_type': 'scheduled',
            'scheduled_time': future_time,
            'frequency': 'daily'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        job_id = response.data['id']
        job = Job.objects.get(id=job_id)
        from jobs.views import JobViewSet
        viewset = JobViewSet()
        viewset.create_periodic_task(job)
        # Check both periodic and enable tasks exist
        self.assertTrue(PeriodicTask.objects.filter(name=f'job-{job_id}').exists())
        self.assertTrue(PeriodicTask.objects.filter(name=f'enable-job-{job_id}').exists())
        # Delete the job
        del_url = reverse('job-detail', args=[job_id])
        del_response = self.client.delete(del_url)
        self.assertEqual(del_response.status_code, status.HTTP_204_NO_CONTENT)
        # Both tasks should be deleted
        self.assertFalse(PeriodicTask.objects.filter(name=f'job-{job_id}').exists())
        self.assertFalse(PeriodicTask.objects.filter(name=f'enable-job-{job_id}').exists())

    def test_update_job_only_pending_and_scheduled_or_interval_integration(self):
        """Integration: Only pending jobs with schedule_type 'interval' or 'scheduled' can be updated."""
        url = reverse('job-list')
        future_time = (timezone.now() + timezone.timedelta(hours=2)).isoformat()
        # Create a pending scheduled job
        data = {
            'job_type': 'send_email',
            'parameters': {
                'subject': 'Integration',
                'body': 'Hello',
                'recipient': 'integration@example.com'
            },
            'schedule_type': 'scheduled',
            'scheduled_time': future_time
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        job_id = response.data['id']
        patch_url = reverse('job-detail', args=[job_id])
        new_time = (timezone.now() + timezone.timedelta(hours=3)).isoformat()
        patch_data = {'scheduled_time': new_time}
        patch_response = self.client.patch(patch_url, patch_data, format='json')
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data['scheduled_time'][:16], new_time[:16])

        # Try to update a job with status 'completed'
        job = Job.objects.get(id=job_id)
        job.status = 'completed'
        job.save()
        patch_response2 = self.client.patch(patch_url, {'scheduled_time': new_time}, format='json')
        self.assertEqual(patch_response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Only pending jobs', str(patch_response2.data))

        # Try to update a job with schedule_type 'immediate'
        data2 = {
            'job_type': 'send_email',
            'parameters': {
                'subject': 'Integration',
                'body': 'Hello',
                'recipient': 'integration2@example.com'
            },
            'schedule_type': 'immediate'
        }
        response2 = self.client.post(url, data2, format='json')
        job_id2 = response2.data['id']
        patch_url2 = reverse('job-detail', args=[job_id2])
        patch_response3 = self.client.patch(patch_url2, {'scheduled_time': new_time}, format='json')
        self.assertEqual(patch_response3.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Only pending jobs', str(patch_response3.data))

        # Try to update a job with schedule_type 'interval' (should succeed)
        data3 = {
            'job_type': 'send_email',
            'parameters': {
                'subject': 'Integration',
                'body': 'Hello',
                'recipient': 'integration3@example.com'
            },
            'schedule_type': 'interval',
            'frequency': 'daily',
            'scheduled_time': future_time
        }
        response3 = self.client.post(url, data3, format='json')
        job_id3 = response3.data['id']
        patch_url3 = reverse('job-detail', args=[job_id3])
        patch_response4 = self.client.patch(patch_url3, {'frequency': 'weekly'}, format='json')
        self.assertEqual(patch_response4.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response4.data['frequency'], 'weekly')
