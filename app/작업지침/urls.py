"""
URL mappings for the 작업지침 app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views, views_db_field

router = DefaultRouter()
router.register(r'관리', views.작업지침_ViewSet, basename="작업지침")
router.register(r'등록', views.작업지침_등록_ViewSet, basename="작업지침_등록")
router.register(r'ECO', views.작업지침_ECO_ViewSet, basename="작업지침_ECO")
router.register(r'이력조회', views.작업지침_이력조회_ViewSet, basename="작업지침_이력조회")
router.register(r'의장도-update', views.작업지침_의장도_Update_ViewSet, basename="작업지침_의장도_Update")

router.register(r'작업지침-process', views.작업지침_Process_ViewSet)
router.register(r'rendering-file', views.작업지침_Rendering_file_ViewSet,  basename='Rendering_file')
router.register(r'첨부-file', views.작업지침_첨부file_ViewSet,  basename='첨부file')
router.register(r'의장도', views.의장도_Viewset,  basename='의장도')

router.register(r'dashboard', views.작업지침_Dashboard_ViewSet, basename='작업지침_dashboard')

# router.register(r'결재', views.작업지침_결재_ViewSet, basename="작업지침_결재")
# router.register(r'결재/결재내용', views.결재내용_ViewSet, basename="작업지침_결재내용")


app_name = '작업지침'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),

    path('db-field-작업지침_관리_View/', views_db_field.DB_Field_작업지침_관리_View.as_view() ),
    path('db-field-작업지침_의장table_View/', views_db_field.DB_Field_작업지침_의장Table_View.as_view() ),

    path('db-field-작업지침_등록_View/', views_db_field.DB_Field_작업지침_등록_View.as_view() ),
    path('db-field-작업지침_ECO_View/', views_db_field.DB_Field_작업지침_ECO_View.as_view() ),
    path('db-field-작업지침_이력조회_View/', views_db_field.DB_Field_작업지침_이력조회_View.as_view() ),
    path('db-field-작업지침_의장도Update_View/', views_db_field.DB_Field_작업지침_의장도Update_View.as_view() ),

]       