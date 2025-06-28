from rest_framework import serializers
from .models import Job
import os
from typing import Any, Dict

# --- Constants for Choices ---
SCHEDULE_TYPE_CHOICES = [
    ('immediate', 'Immediate'),
    ('interval', 'Interval'),
    ('scheduled', 'Scheduled'),
]
FREQUENCY_CHOICES = [
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('hourly', 'Hourly'),
]

# --- Shared Mixin for Schedule Validation ---
class ScheduleValidationMixin:
    def validate_schedule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        schedule_type = data.get('schedule_type', 'immediate')
        scheduled_time = data.get('scheduled_time', None)
        if schedule_type == 'immediate' and scheduled_time:
            raise serializers.ValidationError('scheduled_time must not be set for immediate jobs.')
        if schedule_type == 'scheduled':
            if not scheduled_time:
                raise serializers.ValidationError('scheduled_time is required for scheduled jobs.')
            from django.utils import timezone
            if scheduled_time <= timezone.now():
                raise serializers.ValidationError('scheduled_time must be in the future.')
        return data

# --- Job Serializer ---
class JobSerializer(serializers.ModelSerializer, ScheduleValidationMixin):
    """Serializer for the Job model, including file URL and schedule validation."""
    file_url = serializers.SerializerMethodField()
    schedule_type = serializers.ChoiceField(choices=SCHEDULE_TYPE_CHOICES, default='immediate', required=False)
    scheduled_time = serializers.DateTimeField(required=False, allow_null=True)
    frequency = serializers.ChoiceField(choices=FREQUENCY_CHOICES, default='daily', required=False, allow_blank=True)

    class Meta:
        model = Job
        fields = '__all__'

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # For partial updates, use instance values for missing fields
        instance = getattr(self, 'instance', None)
        schedule_type = data.get('schedule_type')
        scheduled_time = data.get('scheduled_time')
        if instance:
            if schedule_type is None:
                schedule_type = getattr(instance, 'schedule_type', None)
            if scheduled_time is None:
                scheduled_time = getattr(instance, 'scheduled_time', None)
        # Only validate if schedule_type is 'scheduled' or 'interval'
        if schedule_type in ('scheduled', 'interval'):
            if not scheduled_time:
                raise serializers.ValidationError('scheduled_time is required for scheduled or interval jobs.')
            from django.utils import timezone
            if scheduled_time <= timezone.now():
                raise serializers.ValidationError('scheduled_time must be in the future.')
        return data

    def get_file_url(self, obj: Job) -> str:
        if obj.job_type == 'upload_file' and obj.result and isinstance(obj.result, dict):
            return obj.result.get('file_url')
        return None

# --- File Upload Serializer ---
class FileUploadJobSerializer(serializers.Serializer, ScheduleValidationMixin):
    """Serializer for file upload jobs."""
    file = serializers.FileField()
    priority = serializers.IntegerField(default=5)
    max_retries = serializers.IntegerField(default=3)
    schedule_type = serializers.ChoiceField(choices=[('immediate', 'Immediate'), ('scheduled', 'Scheduled')], default='immediate', required=False)
    scheduled_time = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data = self.validate_schedule(data)
        return data

    def validate_file(self, value):
        max_size = 10 * 1024 * 1024  # 10 MB
        if value.size > max_size:
            raise serializers.ValidationError('File size must not exceed 10 MB.')
        return value

    def create(self, validated_data: Dict[str, Any]) -> Job:
        file = validated_data['file']
        file_name = file.name
        temp_dir = 'media/uploads/'
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, file_name)
        with open(temp_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        job = Job.objects.create(
            job_type='upload_file',
            parameters={
                'file_name': file_name,
                'temp_path': temp_path
            },
            priority=validated_data.get('priority', 5),
            max_retries=validated_data.get('max_retries', 3),
            schedule_type=validated_data.get('schedule_type', 'immediate'),
            scheduled_time=validated_data.get('scheduled_time', None)
        )
        return job

# --- Email Message Serializer ---
class EmailMessageSerializer(serializers.Serializer):
    """Serializer for a single personalized email message."""
    recipient = serializers.EmailField()
    subject = serializers.CharField()
    body = serializers.CharField()

# --- Send Email Job Serializer ---
class SendEmailJobSerializer(serializers.Serializer, ScheduleValidationMixin):
    """Serializer for sending single, bulk, or personalized email jobs."""
    recipient = serializers.EmailField(required=False)
    recipients = serializers.ListField(child=serializers.EmailField(), required=False, allow_empty=False)
    emails = EmailMessageSerializer(many=True, required=False)
    subject = serializers.CharField(required=False)
    body = serializers.CharField(required=False)
    priority = serializers.IntegerField(default=5)
    max_retries = serializers.IntegerField(default=3)
    schedule_type = serializers.ChoiceField(choices=[('immediate', 'Immediate'), ('scheduled', 'Scheduled')], default='immediate', required=False)
    scheduled_time = serializers.DateTimeField(required=False, allow_null=True)
    frequency = serializers.ChoiceField(choices=FREQUENCY_CHOICES, default='daily', required=False, allow_blank=True)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data = self.validate_schedule(data)
        recipients = data.get('recipients')
        recipient = data.get('recipient')
        emails = data.get('emails')
        has_single = recipient is not None
        has_bulk = recipients is not None
        has_emails = emails is not None
        if sum([has_single, has_bulk, has_emails]) != 1:
            raise serializers.ValidationError('Provide exactly one of recipient, recipients, or emails.')
        if has_emails:
            if not isinstance(emails, list) or not emails:
                raise serializers.ValidationError('emails must be a non-empty list.')
        else:
            if not data.get('subject') or not data.get('body'):
                raise serializers.ValidationError('subject and body are required for single or bulk email.')
        return data

    def create(self, validated_data: Dict[str, Any]) -> Any:
        jobs = []
        if validated_data.get('emails'):
            for email_obj in validated_data['emails']:
                job = Job.objects.create(
                    job_type='send_email',
                    parameters={
                        'recipient': email_obj['recipient'],
                        'subject': email_obj['subject'],
                        'body': email_obj['body'],
                    },
                    priority=validated_data.get('priority', 5),
                    max_retries=validated_data.get('max_retries', 3),
                    schedule_type=validated_data.get('schedule_type', 'immediate'),
                    scheduled_time=validated_data.get('scheduled_time', None),
                    frequency=validated_data.get('frequency', 'daily'),
                )
                jobs.append(job)
        else:
            recipients = []
            if validated_data.get('recipient'):
                recipients = [validated_data['recipient']]
            elif validated_data.get('recipients'):
                recipients = validated_data['recipients']
            for email in recipients:
                job = Job.objects.create(
                    job_type='send_email',
                    parameters={
                        'recipient': email,
                        'subject': validated_data['subject'],
                        'body': validated_data['body'],
                    },
                    priority=validated_data.get('priority', 5),
                    max_retries=validated_data.get('max_retries', 3),
                    schedule_type=validated_data.get('schedule_type', 'immediate'),
                    scheduled_time=validated_data.get('scheduled_time', None),
                    frequency=validated_data.get('frequency', 'daily'),
                )
                jobs.append(job)
        return jobs if len(jobs) > 1 else jobs[0]
