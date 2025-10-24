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
router.register(r'역량평가사전_DB', views.역량평가사전_DB_ViewSet, basename='v1_역량평가사전_DB')
router.register(r'평가설정_DB', views.평가설정_DB_ViewSet, basename='v1_평가설정_DB')
router.register(r'평가체계_DB', views.평가체계_DB_ViewSet, basename='v1_평가체계_DB')
router.register(r'역량항목_DB', views.역량항목_DB_ViewSet, basename='v1_역량항목_DB')
# router.register(r'역량평가_항목_DB', views.역량평가_항목_DB_ViewSet )

router.register(r'본인평가_DB', views.본인평가_DB_ViewSet, basename='v1_본인평가_DB')
router.register(r'역량_평가_DB', views.역량_평가_DB_ViewSet, basename='v1_역량_평가_DB')
router.register(r'성과_평가_DB', views.성과_평가_DB_ViewSet, basename='v1_성과_평가_DB')
router.register(r'특별_평가_DB', views.특별_평가_DB_ViewSet, basename='v1_특별_평가_DB')

router.register(r'상급자평가_DB', views.상급자평가_DB_ViewSet, basename='v1_상급자평가_DB'  )
router.register(r'평가결과_DB', views.평가결과_DB_ViewSet, basename='v1_평가결과_DB')

router.register(r'평가설정DB_Old', views.평가설정DB_Old_ViewSet, basename='v1_평가설정DB_Old')
router.register(r'종합평가_결과_old', views.종합평가_결과_Old_ViewSet, basename='v1_종합평가_결과_old')

app_name = 'HR평가'

urlpatterns = [
    path('', include(router.urls)),

    path('db-field-역량평가사전_DB_View/', views_db_field.DB_Field_역량평가사전_DB_View.as_view() ),
    path('db-field-평가설정_DB_View/', views_db_field.DB_Field_평가설정_DB_View.as_view() ),


    path('평가체계_db_create/', views.평가체계_DB_API_View.as_view() ),
    path('평가시스템_구축/', views.평가시스템_구축_API_View.as_view() ),
    path('평가설정_DB_Copy_Create/', views.평가설정_DB_Copy_Create_API_View.as_view() ),

    path('종합평가_결과_API_View/', views.종합평가_결과_API_View.as_view() ),

    path('상급자평가_DB_API_View/', views.상급자평가_DB_API_View.as_view() ),
    path('check_평가점수/', views.Check_평가점수_API_View.as_view() ),

    path('db-field-역량_평가_DB_View/', views_db_field.DB_Field_역량_평가_DB_View.as_view() ),
    path('db-field-성과_평가_DB_View/', views_db_field.DB_Field_성과_평가_DB_View.as_view() ),
    path('db-field-특별_평가_DB_View/', views_db_field.DB_Field_특별_평가_DB_View.as_view() ),

    path('db-field-상급자평가_개별_DB_View/', views_db_field.DB_Field_상급자평가_개별_DB_View.as_view() ),
    path('db-field-상급자평가_종합_DB_View/', views_db_field.DB_Field_상급자평가_종합_DB_View.as_view() ),

    path('db-field-종합평가_결과_DB_View/', views_db_field.DB_Field_종합평가_결과_DB_View.as_view() ),
    path('db-field-종합평가_결과_Old_DB_View/', views_db_field.DB_Field_종합평가_결과_Old_DB_View.as_view() ),

    # path('db-field-Elevator_Summary_WO설치일_선택menu_enable_View/', views.DB_Field_Elevator_Summary_WO설치일_선택menu_enable_View.as_view() ),


    ### 5-28 신규
    path('세부평가_Api_View/', views.세부평가_Api_View.as_view() ),

    path('상급자평가_Api_View/', views.상급자평가_Api_View.as_view() ),

    path('평가결과_종합_API_View/', views.평가결과_종합_API_View.as_view() ),
]
