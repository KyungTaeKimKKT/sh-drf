"""
URL mappings for the 생산모니터링 app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views, views_db_field

router = DefaultRouter()
router.register(r'차량관리_기준정보', views.차량관리_기준정보_ViewSet, basename='차량관리_기준정보')
router.register(r'차량관리_운행DB_관리자', views.차량관리_운행DB_관리자_ViewSet, basename='차량관리_운행DB_관리자')
router.register(r'차량관리_운행DB_사용자', views.차량관리_운행DB_사용자_ViewSet, basename='차량관리_운행DB_사용자')
# router.register(r'개인리스트-개인', views.개인_리스트_DB_개인_ViewSet, basename='개인_리스트_DB_개인')
# router.register(r'조직리스트-전사', views.조직_리스트_DB_전사_ViewSet, basename='조직_리스트_DB_전사')
# router.register(r'조직리스트-개인', views.조직_리스트_DB_개인_ViewSet, basename='조직_리스트_DB_개인')
# router.register(r'전기사용량', views.전기사용량_ViewSet, basename='전기사용량')

# router.register(r'개인리스트-이력조회-개인', views.개인_리스트_DB_개인_조회_ViewSet, basename='개인_리스트_DB_이력조회_개인')
# router.register(r'개인리스트-이력조회-전사', views.개인_리스트_DB_전사_조회_ViewSet, basename='개인_리스트_DB_이력조회_전사')
# router.register(r'조직리스트-이력조회-개인', views.조직_리스트_DB_개인_조회_ViewSet, basename='조직_리스트_DB_이력조회_개인')
# router.register(r'조직리스트-이력조회-전사', views.조직_리스트_DB_전사_조회_ViewSet, basename='조직_리스트_DB_이력조회_전사')

# router.register(r'휴일등록', views.휴일등록_DB_개인_ViewSet, basename='휴일등록')

app_name = '차량관리'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),

    path('db-field-차량관리_기준정보_View/', views_db_field.DB_Field_차량관리_기준정보_View.as_view() ),
    path('db-field-차량관리_운행DB_관리자_View/', views_db_field.DB_Field_차량관리_운행DB_관리자_View.as_view() ),
    path('db-field-차량관리_운행DB_사용자_View/', views_db_field.DB_Field_차량관리_운행DB_사용자_View.as_view() ),
    path('차량관리_차량번호_사용자_API_View/', views.차량관리_차량번호_사용자_API_View.as_view() ),
]
