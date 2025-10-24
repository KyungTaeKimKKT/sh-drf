"""
URL mappings for the csvupload app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from . import views, views_db_field


router = DefaultRouter()
router.register(r'관리', views.영업수주_관리_ViewSet, basename='영업수주_관리')
router.register(r'일정관리', views.영업수주_일정_ViewSet, basename='영업수주_일정관리')
router.register(r'금액관리', views.영업수주_금액_ViewSet, basename='영업수주_금액관리')
# router.register(r'배포리스트', views.Release배포_ViewSet, basename='배포리스트')
router.register(r'자재내역_To_의장_Mapping_DB', views.자재내역_To_의장_Mapping_ViewSet, basename='자재내역_To_의장_Mapping')
# router.register(r'chat-내용', views.Chat_내용_ViewSet, basename='chat-내용') 
# router.register(r'chat-file', views.Chat_file_ViewSet, basename='chat-file')


app_name = '영업수주'

urlpatterns = [
    path('', include(router.urls)),

    path('db-field-영업수주_관리_DB_View/', views_db_field.DB_Field_영업수주_관리DB_View.as_view() ),

    path('db-field-영업수주_자재내역_To_의장_Mapping_DB_View/', views_db_field.DB_Field_영업수주_자재내역_To_의장DB_View.as_view() ),

    path('영업수주_등록_ApiProcess/', views.Process_영업수주_등록_Api.as_view() ),

    path('simulation/', views.영업수주_Simulation_Api.as_view() ),

    path('영업수주_금액_Summary_Api/', views.영업수주_Summary_Api.as_view() ),

]

