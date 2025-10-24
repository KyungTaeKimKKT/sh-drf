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
router.register(r'배포관리', views.Release관리_ViewSet, basename='관리')
router.register(r'배포리스트', views.Release배포_ViewSet, basename='배포리스트')
# router.register(r'chat-내용', views.Chat_내용_ViewSet, basename='chat-내용') 
# router.register(r'chat-file', views.Chat_file_ViewSet, basename='chat-file')


app_name = 'release'

urlpatterns = [
    path('', include(router.urls)),


]