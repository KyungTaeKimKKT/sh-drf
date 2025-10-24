"""
URL mappings for the 공지요청사항 app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'공지사항', views.공지사항_ViewSet, basename="공지사항")
router.register(r'공지사항-사용자', views.공지사항_사용자_ViewSet, basename="공지사항_사용자")

router.register(r'공지사항-reading', views.공지사항_Reading_ViewSet, basename='공지사항Reading')

router.register(r'요청사항-관리', views.요청사항_DB_ViewSet, basename="요청사항_관리")
router.register(r'요청사항-사용자', views.요청사항_DB_사용자ViewSet, basename="요청사항_사용자")
router.register(r'요청사항-file', views.File_for_Request_ViewSet, basename='요청사항-file')



app_name = '공지요청사항'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),

]       