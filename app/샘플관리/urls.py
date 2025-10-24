"""
URL mappings for the 샘플관리 app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views, views_db_field

router = DefaultRouter()
router.register(r'관리', views.샘플관리_샘플관리_ViewSet, basename="관리")
router.register(r'의뢰', views.샘플관리_샘플의뢰_ViewSet, basename="의뢰")
router.register(r'완료', views.샘플관리_샘플완료_ViewSet, basename="완료")
router.register(r'이력조회', views.샘플관리_이력조회_ViewSet, basename="이력조회")

router.register(r'샘플관리-process', views.샘플관리_Process_ViewSet, basename="process")

router.register(r'샘플관리-첨부file', views.샘플관리_첨부file_ViewSet, basename="첨부파일")
router.register(r'샘플관리-완료file', views.샘플관리_완료file_ViewSet, basename="완료파일")

app_name = '샘플관리'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),

    path('db-field-샘플관리_샘플관리_View/', views_db_field.DB_Field_샘플관리_샘플관리_View.as_view() ),
    path('db-field-샘플관리_샘플의뢰_View/', views_db_field.DB_Field_샘플관리_샘플의뢰_View.as_view() ),
    path('db-field-샘플관리_샘플완료_View/', views_db_field.DB_Field_샘플관리_샘플완료_View.as_view() ),
    path('db-field-샘플관리_이력조회_View/', views_db_field.DB_Field_샘플관리_이력조회_View.as_view() ),
    
    path('db-field-샘플관리_Process_View/', views_db_field.DB_Field_샘플관리_샘플의뢰_의장Table_View.as_view() ),

]       