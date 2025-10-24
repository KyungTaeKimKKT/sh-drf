"""
URL mappings for the scraping app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'정부기관-db', views.정부기관_DB_ViewSet, basename="정부기관-db")
router.register(r'정부기관news', views.NEWS_DB_ViewSet, basename='정부기관news')
router.register(r'정부기관news-tablehead관리', views.NEWS_Table_Head_DB_ViewSet, basename='정부기관news-tablehead관리')
router.register(r'정부기관news-log', views.NEWS_LOG_DB_ViewSet, basename='정부기관news-log')

app_name = 'scraping'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),
    
    path('db-field-NEWS_DB_View/', views.DB_Field_NEWS_DB_View.as_view() ),

]       