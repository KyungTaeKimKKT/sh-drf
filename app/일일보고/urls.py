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
router.register(r'개인리스트-전사', views.개인_리스트_DB_전사_보고용_ViewSet, basename='개인_리스트_DB_전사')
router.register(r'개인리스트-개인', views.개인_리스트_DB_개인_ViewSet, basename='개인_리스트_DB_개인')
router.register(r'조직리스트-전사', views.조직_리스트_DB_전사_보고용_ViewSet, basename='조직_리스트_DB_전사')
router.register(r'조직리스트-개인', views.조직_리스트_DB_개인_ViewSet, basename='조직_리스트_DB_개인')
router.register(r'전기사용량', views.전기사용량_ViewSet, basename='전기사용량')

router.register(r'개인리스트-이력조회-개인', views.개인_리스트_DB_개인_조회_ViewSet, basename='개인_리스트_DB_이력조회_개인')
router.register(r'개인리스트-이력조회-전사', views.개인_리스트_DB_전사_조회_ViewSet, basename='개인_리스트_DB_이력조회_전사')
router.register(r'조직리스트-이력조회-개인', views.조직_리스트_DB_개인_조회_ViewSet, basename='조직_리스트_DB_이력조회_개인')
router.register(r'조직리스트-이력조회-전사', views.조직_리스트_DB_전사_조회_ViewSet, basename='조직_리스트_DB_이력조회_전사')

router.register(r'개인리스트-팀별조회-개인', views.개인_리스트_DB_팀별_조회_ViewSet, basename='개인_리스트_DB_팀별_조회_개인')

router.register(r'휴일등록', views.휴일등록_DB_개인_ViewSet, basename='휴일등록')

app_name = '일일보고'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),



]
