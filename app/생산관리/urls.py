"""
URL mappings for the 생산관리 app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views, views_db_field

router = DefaultRouter()
router.register(r'생산계획-일정관리', views.생산계획_일정관리_ViewSet, basename="생산계획")
router.register(r'생산계획-schedule-by-types', views.생산계획_Schedule_By_Types_ViewSet )
router.register(r'생산계획-확정-branch', views.생산계획_확정_Branch_ViewSet, basename='생산계획_확정_Branch')
router.register(r'생산실적', views.생산실적_ViewSet, basename='생산실적')
router.register(r'생산관리-제품완료', views.생산관리_제품완료_ViewSet, basename='생산관리-제품완료')

router.register(r'생산계획-공정상세', views.생산계획_공정상세_ViewSet, basename='생산계획-공정상세')

# router.register(r'history', views.History_ViewSet, basename="history_변경내역")
router.register(r'생산계획-dday', views.생산계획_DDay_ViewSet, basename='생산계획-dday')
router.register(r'생산계획-productionline', views.ProductionLine_ViewSet, basename='생산계획-productionline')
router.register(r'생산관리-판금처DB', views.판금처_DB_ViewSet, basename='생산관리-판금처DB')


app_name = '생산관리'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),

    path('db-field-생산계획_일정관리_View/', views_db_field.DB_Field_생산계획_일정관리_View.as_view() ),
    
    path('db-field-생산계획_공정상세_View/', views_db_field.DB_Field_생산계획_공정상세_View.as_view() ),
    path('db-field-생산계획_공정상세_Merged_View/', views_db_field.DB_Field_생산계획_공정상세_Merged_View.as_view() ),
    # path('계획관리/', views.생산계획_생성.as_view() ),
    # path('요약/', views.생산지시_요약_List.as_view() ),


]       