from rest_framework import serializers
from .models import Job
import os

class JobSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = '__all__'

    def get_file_url(self, obj):
        if obj.job_type == 'upload_file' and obj.result and isinstance(obj.result, dict):
            return obj.result.get('file_url')
        return None

class FileUploadJobSerializer(serializers.Serializer):
    file = serializers.FileField()
    file_name = serializers.CharField(max_length=255)
    priority = serializers.IntegerField(default=5)
    max_retries = serializers.IntegerField(default=3)

    def create(self, validated_data):
        file = validated_data['file']
        file_name = validated_data['file_name']
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
            max_retries=validated_data.get('max_retries', 3)
        )
        return job
