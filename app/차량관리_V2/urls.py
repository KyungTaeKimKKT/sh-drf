"""
URL mappings for the 생산모니터링 app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'차량관리_기준정보', views.차량관리_V2_기준정보_ViewSet, basename='v2_차량관리_기준정보')
router.register(r'차량관리_운행관리_관리자', views.차량관리_V2_운행DB_관리자_ViewSet, basename='v2_차량관리_운행관리_관리자')
router.register(r'차량관리_운행관리_사용자', views.차량관리_V2_운행DB_사용자_ViewSet, basename='v2_차량관리_운행관리_사용자')
router.register(r'차량관리_운행관리_조회', views.차량관리_V2_운행DB_조회_ViewSet, basename='v2_차량관리_운행관리_조회')

app_name = '차량관리_V2'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),
    path('old-db-migrate/', views.차량관리_V2_DB_Migrate_API_View.as_view() ),
]
