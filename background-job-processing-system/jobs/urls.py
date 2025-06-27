from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobViewSet, TestWebSocketView

router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='job')

urlpatterns = [
    path('', include(router.urls)),
    path('jobs/send-email/', JobViewSet.as_view({'post': 'send_email'}), name='job-send-email'),
    path('jobs/upload-file/', JobViewSet.as_view({'post': 'upload_file_standalone'}), name='job-upload-file-standalone'),
]

urlpatterns.append(path('test-websocket/',
                   TestWebSocketView.as_view(), name='test_websocket'))

