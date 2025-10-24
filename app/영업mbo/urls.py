"""
URL mappings for the 영업mbo app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views, views_db_field

router = DefaultRouter()
router.register(r'출하현장_master_DB', views.출하현장_master_DB_ViewSet, basename="출하현장_master_DB")
router.register(r'신규현장_등록_DB', views.신규현장_등록_DB_ViewSet, basename="신규현장_등록_DB")
router.register(r'사용자등록_DB', views.사용자등록_DB_ViewSet, basename="사용자등록_DB")

router.register(r'신규현장_등록_DB_관리자용', views.신규현장_등록_DB_관리자용_ViewSet, basename="신규현장_등록_DB_관리자용")


# router.register(r'개인별_DB', views.개인별_DB_ViewSet, basename="개인별_DB")
router.register(r'관리자등록_DB', views.관리자등록_DB_ViewSet, basename="관리자등록_DB")
router.register(r'영업mbo_설정DB', views. 영업mbo_설정DB_ViewSet, basename="영업mbo_설정DB")
router.register(r'영업mbo_엑셀등록', views.영업mbo_엑셀등록_ViewSet, basename="영업mbo_엑셀등록")
router.register(r'고객사_DB', views.고객사_DB_ViewSet, basename="고객사_DB")
router.register(r'구분_DB', views.구분_DB_ViewSet, basename="구분_DB")
router.register(r'기여도_DB', views.기여도_DB_ViewSet, basename="기여도_DB")
router.register(r'사용자_DB', views.사용자_DB_ViewSet, basename="사용자_DB")

### report

router.register(r'년간보고_지사_고객사', views.년간보고_지사_고객사_ViewSet, basename="년간보고_지사_고객사")
router.register(r'년간보고_지사_구분', views.년간보고_지사_구분_ViewSet, basename="년간보고_지사_구분")
router.register(r'년간보고_개인별', views.년간보고_개인별_ViewSet, basename="년간보고_개인별")


router.register(r'년간보고_달성률_기준', views.년간보고_달성률_기준_ViewSet, basename="년간보고_달성률_기준")
router.register(r'보고기준_DB', views.보고기준_DB_ViewSet, basename="보고기준_DB")


app_name = '영업mbo'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),
    #### 😀 dashboard 용이므로 나중에 수정 24-12-03k
    path('DB-fields/년간보고_지사_고객사', views.DB_Field_년간보고_지사_고객사.as_view(), name='db_fields_년간보고_지사_고객사'),
    # path('계획관리/', views.생산계획_생성.as_view() ),

    path('db-field-영업mbo_설정DB_View/', views_db_field.DB_Field_영업mbo_설정DB_View.as_view() ),
    path('db-field-영업mbo_신규현장_등록_DB_View/', views_db_field.DB_Field_사용자등록_View.as_view() ),
    path('db-field-영업mbo_신규현장_등록_DB_관리자용_View/', views_db_field.DB_Field_관리자등록_View.as_view() ),

    path('db-field-영업mbo_년간보고_지사_고객사_View/', views_db_field.DB_Field_년간보고_지사_고객사_View.as_view(), name='db_fields_년간보고_지사_고객사'),
    path('db-field-영업mbo_년간보고_지사_구분_View/', views_db_field.DB_Field_년간보고_지사_구분_View.as_view(), name='db_fields_년간보고_지사_구분'),
    path('db-field-영업mbo_년간보고_개인별_View/', views_db_field.DB_Field_년간보고_개인별_View.as_view(), name='db_fields_년간보고_개인별'),

    path('db-field-영업mbo_년간목표입력_지사_구분_View/', views_db_field.DB_Field_년간목표입력_지사_구분_View.as_view(), name='db_fields_년간목표입력_지사_구분'),
    path('db-field-영업mbo_년간목표입력_개인별_View/', views_db_field.DB_Field_년간목표입력_개인별_View.as_view(), name='db_fields_년간목표입력_개인별'),

    path('db-field-영업mbo_이력조회_View/', views_db_field.DB_Field_이력조회_View.as_view(), name='db_fields_이력조회고'),

    path('사용자마감_apiview/', views.사용자마감_View.as_view() ),
    path('관리자마감_apiview/', views.관리자마감_View.as_view() ),

    path('년간목표생성_apiview/', views.년간목표생성_View.as_view() ),
    #### 📌 25-5.13 추가
    path('영업MBO_보고서_apiview/', views.영업MBO_보고서_ApiViewSet.as_view() ),
    path('영업MBO_보고서_지사_고객사_apiview/', views.영업MBO_보고서_지사_고객사_ApiView.as_view() ),
    path('영업MBO_보고서_개인별_apiview/', views.영업MBO_보고서_개인별_ApiView.as_view() ),

    path('get-매출년도list/', views.영업MBO_매출년도_API_View.as_view() ),
]       
