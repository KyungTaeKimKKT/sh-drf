"""
URL mappings for the 샘플관리 app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views, views_db

router = DefaultRouter()
router.register(r'관리', views.망관리_DB_ViewSet, basename="관리")
router.register(r'등록', views.망관리_등록_ViewSet, basename="등록")
# router.register(r'완료', views.샘플완료_ViewSet, basename="완료")
router.register(r'이력조회', views.망관리_이력조회_ViewSet, basename="이력조회")



app_name = '망관리'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),

    path('db-field-망관리_DB_View/', views_db.DB_Field_망관리_DB_View.as_view() ),
    path('db-field-망관리_등록_View/', views_db.DB_Field_망관리_등록_View.as_view() ),
    path('db-field-망관리_이력조회_View/', views_db.DB_Field_망관리_이력조회_View.as_view() ),

]       