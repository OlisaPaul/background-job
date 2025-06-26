from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobViewSet, TestWebSocketView

router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='job')

urlpatterns = [
    path('', include(router.urls)),
]

urlpatterns.append(path('test-websocket/',
                   TestWebSocketView.as_view(), name='test_websocket'))

