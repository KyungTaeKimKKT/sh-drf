"""
URL mappings for the csvupload app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register(r'job-info', views.JOB_INFO_ViewSet, basename='job-info')
router.register(r'scheduler-job', views.Scheduler_Job_ViewSet, basename='scheduler-job')
router.register(r'scheduler-job-status', views.Scheduler_Job_Status_ViewSet, basename='scheduler-job-status')
router.register(r'scheduler-job-log', views.Scheduler_Job_Log_ViewSet, basename='scheduler-job-log')

app_name = 'scheduler_job'

urlpatterns = [
    path('', include(router.urls)),
    path('job-names-only/', views.Scheduler_Job_Names_ApiView.as_view(), name='job-names'),

]