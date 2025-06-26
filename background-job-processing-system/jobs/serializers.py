from rest_framework import serializers
from .models import Job
import os

class JobSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    schedule_type = serializers.ChoiceField(choices=[
        ('immediate', 'Immediate'),
        ('hourly', 'Every Hour'),
        ('daily', 'Every Day'),
        ('monthly', 'Every Month'),
        ('yearly', 'Every Year'),
        ('yearly', 'sche'),
    ], default='immediate', required=False)
    scheduled_time = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = Job
        fields = '__all__'

    def get_file_url(self, obj):
        if obj.job_type == 'upload_file' and obj.result and isinstance(obj.result, dict):
            return obj.result.get('file_url')
        return None

class FileUploadJobSerializer(serializers.Serializer):
    file = serializers.FileField()
    priority = serializers.IntegerField(default=5)
    max_retries = serializers.IntegerField(default=3)
    schedule_type = serializers.ChoiceField(choices=[
        ('immediate', 'Immediate'),
        ('one-off', 'One-off Scheduled'),
        ('hourly', 'Every Hour'),
        ('daily', 'Every Day'),
        ('monthly', 'Every Month'),
        ('yearly', 'Every Year'),
    ], default='immediate', required=False)
    scheduled_time = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, data):
        # Disallow recurring file upload jobs, but allow immediate and one-off scheduled
        recurring_types = ['hourly', 'daily', 'monthly', 'yearly']
        if data.get('schedule_type', 'immediate') in recurring_types:
            raise serializers.ValidationError('Recurring file upload jobs are not supported. Please use immediate or one-off scheduled upload.')
        return data

    def validate_file(self, value):
        max_size = 10 * 1024 * 1024  # 10 MB
        if value.size > max_size:
            raise serializers.ValidationError('File size must not exceed 10 MB.')
        return value

    def create(self, validated_data):
        file = validated_data['file']
        file_name = file.name
        # Save file temporarily to disk (media/uploads/)
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
