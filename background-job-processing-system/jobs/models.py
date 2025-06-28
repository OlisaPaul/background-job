from django.db import models
from typing import Any

# --- Constants for Choices and Statuses ---
JOB_TYPE_CHOICES = [
    ('send_email', 'Send Email'),
    ('process_image', 'Process Image'),
    ('generate_report', 'Generate Report'),
    ('backup_database', 'Backup Database'),
    ('fetch_data', 'Fetch Data'),
    ('batch_process', 'Batch Process'),
    ('send_notification', 'Send Notification'),
    ('cleanup_files', 'Cleanup Files'),
    ('upload_file', 'Upload File to S3'),
]

SCHEDULE_TYPE_CHOICES = [
    ('immediate', 'Immediate'),
    ('scheduled', 'Scheduled'),
    ('interval', 'Interval'),
]

FREQUENCY_CHOICES = [
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('hourly', 'Hourly'),
]

JOB_STATUS_PENDING = 'pending'
JOB_STATUS_RUNNING = 'running'
JOB_STATUS_COMPLETED = 'completed'
JOB_STATUS_FAILED = 'failed'

class Job(models.Model):
    """
    Model representing a background job of various types (email, file upload, etc).
    Stores parameters, status, scheduling, and result.
    """
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    parameters = models.JSONField()
    status = models.CharField(max_length=20, default=JOB_STATUS_PENDING)
    priority = models.IntegerField(default=5)
    max_retries = models.IntegerField(default=3)
    retries = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    result = models.JSONField(null=True, blank=True)
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPE_CHOICES, default='immediate')
    scheduled_time = models.DateTimeField(null=True, blank=True)
    frequency = models.CharField(choices=FREQUENCY_CHOICES, blank=True, null=True, default='daily')

    def __str__(self) -> str:
        return f"{self.job_type} (Priority: {self.priority})"
