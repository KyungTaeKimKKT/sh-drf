"""
URL mappings for the 디자인관리 app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'관리', views.디자인관리_ViewSet, basename='디자인관리-전체')
router.register(r'의뢰', views.디자인관리_의뢰_ViewSet, basename='디자인관리-의뢰')
router.register(r'재의뢰', views.디자인관리_재의뢰_ViewSet, basename='디자인관리-재의뢰')
router.register(r'접수', views.디자인관리_접수_ViewSet, basename='디자인관리-접수')
router.register(r'완료', views.디자인관리_완료_ViewSet, basename='디자인관리-완료')
router.register(r'이력조회', views.디자인관리_이력조회_ViewSet, basename='디자인관리-이력조회')

router.register(r'의뢰file-viewSet', views.의뢰file_ViewSet, basename='디자인관리-의뢰file-viewset')
router.register(r'완료file-viewSet', views.완료file_ViewSet, basename='디자인관리-완료file-viewset')

router.register(r'group의뢰', views.Group의뢰_ViewSet, basename='Group의뢰')

# router.register(r'db정리', views.DB_정리_의뢰차수, basename='DB_정리_의뢰차수')

app_name = '디자인관리'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),

    path('db정리/', views.DB_정리_의뢰차수.as_view() ),
    path('dashbord/', views.dashBoard_ViewSet.as_view() ),

    path('db-field-디자인관리_View/', views.DB_Field_디자인관리_View.as_view() ),
    path('db-field-디자인의뢰_View/', views.DB_Field_디자인의뢰_View.as_view() ),
    path('db-field-디자인접수_View/', views.DB_Field_디자인접수_View.as_view() ),
    path('db-field-디자인완료_View/', views.DB_Field_디자인완료_View.as_view() ),
    path('db-field-이력조회_View/', views.DB_Field_이력조회_View.as_view() ),
    path('db-field-디자인재의뢰_View/', views.DB_Field_디자인재의뢰_View.as_view() ),
]