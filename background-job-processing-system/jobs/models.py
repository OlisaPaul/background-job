from django.db import models

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
]

class Job(models.Model):
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    parameters = models.JSONField()
    status = models.CharField(max_length=20, default='pending')
    priority = models.IntegerField(default=5)
    max_retries = models.IntegerField(default=3)
    retries = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    result = models.JSONField(null=True, blank=True)
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPE_CHOICES, default='immediate')
    scheduled_time = models.DateTimeField(null=True, blank=True)
    frequency = models.CharField(choices=[
        ('daily', 'Daily'), 
        ('weekly', 'Weekly'), 
        ('monthly', 'Monthly'), 
        ('hourly', 'Hourly')
    ], blank=True, null=True, default='daily')

    def __str__(self):
        return f"{self.job_type} (Priority: {self.priority})"
