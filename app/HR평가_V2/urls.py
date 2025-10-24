"""
URL mappings for the csvupload app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register(r'역량평가사전_DB', views.역량평가사전_DB_ViewSet, basename='v2_역량평가사전_DB')
router.register(r'평가설정_DB', views.평가설정_DB_ViewSet, basename='v2_평가설정_DB')
router.register(r'평가체계_DB', views.평가체계_DB_ViewSet, basename='v2_평가체계_DB')

router.register(r'역량평가_항목_DB', views.역량평가_항목_DB_ViewSet, basename='v2_역량평가_항목_DB')
# router.register(r'역량항목_DB', views.역량항목_DB_ViewSet )
# router.register(r'역량평가_항목_DB', views.역량평가_항목_DB_ViewSet )

# router.register(r'본인평가_DB', views.본인평가_DB_ViewSet)
# router.register(r'역량_평가_DB', views.역량_평가_DB_ViewSet)
# router.register(r'성과_평가_DB', views.성과_평가_DB_ViewSet)
# router.register(r'특별_평가_DB', views.특별_평가_DB_ViewSet)

# router.register(r'상급자평가_DB', views.상급자평가_DB_ViewSet )
# router.register(r'평가결과_DB', views.평가결과_DB_ViewSet )

# router.register(r'평가설정DB_Old', views.평가설정DB_Old_ViewSet )
# router.register(r'종합평가_결과_old', views.종합평가_결과_Old_ViewSet )

app_name = 'HR평가_V2'

urlpatterns = [
    path('', include(router.urls)),

    path('기존평가설정_복사/', views.OLD_Copy_View.as_view() ),
    path('평가결과_마이그레이션/', views.지난평가결과_copy_to_V2_View.as_view() ),
    path('평가결과_마이그레이션_초기화/', views.Migration_Init_View.as_view() ),

    path('세부평가_Api_View/', views.세부평가_Api_View.as_view() ),
    path('상급자평가_Api_View/', views.상급자평가_Api_View.as_view() ),

    path('상급자평가_BatchUpdate_Api_View/', views.상급자평가_BatchUpdate_Api_View.as_view() ),

    path('평가결과_종합_API_View/', views.평가결과_종합_API_View.as_view() ),


    # path('평가체계_db_create/', views.평가체계_DB_API_View.as_view() ),
    # path('평가시스템_구축/', views.평가시스템_구축_API_View.as_view() ),
    # path('평가설정_DB_Copy_Create/', views.평가설정_DB_Copy_Create_API_View.as_view() ),

    # path('종합평가_결과_API_View/', views.종합평가_결과_API_View.as_view() ),

    # path('상급자평가_DB_API_View/', views.상급자평가_DB_API_View.as_view() ),
    # path('check_평가점수/', views.Check_평가점수_API_View.as_view() ),


    # # path('db-field-Elevator_Summary_WO설치일_선택menu_enable_View/', views.DB_Field_Elevator_Summary_WO설치일_선택menu_enable_View.as_view() ),


    # ### 5-28 신규
    # path('세부평가_Api_View/', views.세부평가_Api_View.as_view() ),

    # path('상급자평가_Api_View/', views.상급자평가_Api_View.as_view() ),

    # path('평가결과_종합_API_View/', views.평가결과_종합_API_View.as_view() ),
]
