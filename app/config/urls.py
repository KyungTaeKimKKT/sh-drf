"""
URL mappings for the config app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'table_config', views.Table_Config_ViewSet, basename='table_config')
router.register(r'cache', views.Cache_ViewSet, basename='cache')
router.register(r'resources', views.Resources_ViewSet, basename='resources')
router.register(r'ws_urls_db', views.WS_URLS_DB_ViewSet, basename='ws_urls_db')
# router.register(r'ws_urls_db', views.WS_URLS_DB_ViewSet, basename='ws_urls_db')
router.register(r'table_menus', views.Table_ViewSet, basename='table')
router.register(r'v_header_menus', views.V_Header_Menus_ViewSet, basename='v_header_menus')
router.register(r'h_header_menus', views.H_Header_Menus_ViewSet, basename='h_header_menus')
router.register(r'cell_menus', views.Cell_Menus_ViewSet, basename='cell_menus')
router.register(r'table_v_header_link', views.TableVHeaderLink_ViewSet, basename='table_v_header_link')
router.register(r'table_h_header_link', views.TableHHeaderLink_ViewSet, basename='table_h_header_link')
router.register(r'table_cell_menu_link', views.TableCellMenuLink_ViewSet, basename='table_cell_menu_link')

router.register(r'table_only_name', views.Table_Only_Name_ViewSet, basename='table_only_name')

router.register(r'color_scheme', views.ColorScheme_ViewSet, basename='color_scheme')


app_name = 'config'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),
    
    # path('cache/', views.Cache_ViewSet.as_view() ),
    # path('cache', views.Cache_ViewSet.as_view() ),


#     path('db정리/', views.DB_정리_의뢰차수.as_view() ),
#     path('dashbord/', views.dashBoard_ViewSet.as_view() ),

#     path('db-field-디자인관리_View/', views.DB_Field_디자인관리_View.as_view() ),
#     path('db-field-디자인의뢰_View/', views.DB_Field_디자인의뢰_View.as_view() ),
#     path('db-field-디자인접수_View/', views.DB_Field_디자인접수_View.as_view() ),
#     path('db-field-디자인완료_View/', views.DB_Field_디자인완료_View.as_view() ),
#     path('db-field-이력조회_View/', views.DB_Field_이력조회_View.as_view() ),
#     path('db-field-디자인재의뢰_View/', views.DB_Field_디자인재의뢰_View.as_view() ),
]