from django.urls import re_path
from . import consumers

# WebSocket URL patterns for job status updates
websocket_urlpatterns = [
    re_path(r'ws/jobs/status/$', consumers.JobStatusConsumer.as_asgi()),
]
