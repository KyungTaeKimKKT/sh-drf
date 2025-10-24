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
router.register(r'chat-room', views.Chat_Room_ViewSet, basename='chat-room')
router.register(r'chat-내용', views.Chat_내용_ViewSet, basename='chat-내용') 
router.register(r'chat-file', views.Chat_file_ViewSet, basename='chat-file')


app_name = 'messagebox'

urlpatterns = [
    path('', include(router.urls)),

    # path(r'관리/generate-summary-wo설치일/', views.관리_Summary_WO설치일, name='elevator-summary-wo설치일-관리' ),

]