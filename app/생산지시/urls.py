"""
URL mappings for the 생산지시 app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views, views_db_field

router = DefaultRouter()
router.register(r'관리', views.생산지시_ViewSet, basename="생산지시")
router.register(r'spg', views.SPG_ViewSet, basename="SPG")
router.register(r'spg-table', views.SPG_Table_ViewSet, basename='SPG-Table')
router.register(r'spg-file', views.SPG_File_ViewSet, basename='SPG-File')
router.register(r'tab-made-file', views.TAB_Made_file_Viewset, basename='TAB_Made_file')

# router.register(r'JAMB관리', views.생산지시_JAMB_ViewSet, basename="생산지시_JAMB")
router.register(r'JAMB-file', views.JAMB_file_ViewSet,  basename="생산지시_JAMB_file" )
router.register(r'JAMB-발주정보' , views.JAMB_발주정보_ViewSet, basename="생산지시_JAMB_발주정보")

router.register(r'도면정보-table' , views.도면정보_Table_ViewSet, basename="생산지시_도면정보_Table")
router.register(r'HTM-table' , views.HTM_Table_ViewSet, basename="생산지시_HTM_Table")

# router.register(r'생산지시-배포',  views.생산지시_배포_ViewSet, basename='생산지시_배포')
# router.register(r'생산지시-배포-생산계획대기',  views.생산지시_배포_생산계획대기_ViewSet, basename='생산지시_배포_생산계획대기')




app_name = '생산지시'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),

    path('db-field-생산지시_관리_View/', views_db_field.DB_Field_생산지시_관리_View.as_view() ),
    path('db-field-생산지시_의장table_View/', views_db_field.DB_Field_생산지시_의장Table_View.as_view() ),
    path('db-field-생산지시_도면정보table_View/', views_db_field.DB_Field_생산지시_도면정보Table_Body_View.as_view() ),
    path('db-field-생산지시_spg_table_View/', views_db_field.DB_Field_생산지시_SPG_Table_View.as_view() ),
    
    # path('db-field-생산지시_등록_View/', views_db_field.DB_Field_생산지시_등록_View.as_view() ),
    # path('db-field-생산지시_ECO_View/', views_db_field.DB_Field_생산지시_ECO_View.as_view() ),
    # path('db-field-생산지시_이력조회_View/', views_db_field.DB_Field_생산지시_이력조회_View.as_view() ),
    # path('db-field-생산지시_의장도Update_View/', views_db_field.DB_Field_생산지시_의장도Update_View.as_view() ),


]       