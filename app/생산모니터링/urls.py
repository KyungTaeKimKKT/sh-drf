"""
URL mappings for the 생산모니터링 app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views, views_db_field, views_new

router = DefaultRouter()
router.register(r'KISOK/당일계획실적', views.KIOSK_생산계획실적ViewSet, basename='kiosk-production-plan')
router.register(r'생산현황/당일계획', views.당일생산계획ViewSet, basename='daily-production-plan')
router.register(r'sensor-기준정보', views.sensor_기준정보ViewSet, basename='sensor-standard-info')
router.register(r'생산현황/당일계획-센서용', views.당일생산계획_for_sensor_ViewSet, basename='production-plan-for-sensor')
router.register(r'무재해db', views.무재해_DB_ViewSet, basename='safety-db')
router.register(r'생산현황/당일계획-background용', views.당일생산계획_bg용_ViewSet, basename='production-plan-for-background')

router.register(r'new/무재해db', views_new.무재해_DB_ViewSet, basename='new-safety-db')
router.register(r'new/Sensor_기준정보', views_new.Sensor_기준정보_ViewSet, basename='new-sensor-standard-info')
router.register(r'new/휴식시간_DB', views_new.휴식시간_DB_ViewSet, basename='new-break-time-db')
router.register(r'new/생산계획실적_DB', views_new.생산계획실적_DB_ViewSet, basename='new-production-plan-db')

app_name = '생산모니터링'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),

    path('db-field-생산계획실적_View/', views_db_field.DB_Field_생산계획실적_View.as_view() ),


    path('api-view/예상생산실적_View/', views_new.예상생산실적_View.as_view() ),
    # path('', views.생산모니터링_profile, name="생산모니터링_profile"),


]       