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
router.register(r'csvupload', views.CsvUploadViewSet)
router.register(r'info/summary_wo설치일', views.Summary_WO설치일_ViewSet) 
router.register(r'info/승강기협회', views.승강기협회_ViewSet ) 


app_name = 'Elevator-info'

urlpatterns = [
    path('', include(router.urls)),

    path(r'관리/generate-summary-wo설치일/', views.관리_Summary_WO설치일, name='elevator-summary-wo설치일-관리' ),
    path(r'info/summary-wo설치일-download/', views.Summary_WO설치일_FileDownload, name='summary-wo설치일-download'), 
    path(r'info/승강기협회-download/', views.승강기협회_FileDownload, name='승강기협회-download'), 

]