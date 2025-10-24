"""
URL mappings for the rtsp_cam.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'ai_models', views.AIModelViewSet, basename='ai_models')
router.register(r'hi_camera_settings', views.RTSPCameraSettingViewSet, basename='hi_camera_settings')


app_name = 'rtsp_cam'    

urlpatterns = [
    path('', include(router.urls)),


]