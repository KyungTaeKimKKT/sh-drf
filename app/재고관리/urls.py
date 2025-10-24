"""
URL mappings for the 재고관리 app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views, views_db_field

router = DefaultRouter()
router.register(r'warehouse', views.Warehouse_ViewSet, basename="재고관리_warehouse")
router.register(r'stock', views.Stock_ViewSet, basename="재고관리_stock")
router.register(r'stock-history', views.StockHistory_ViewSet, basename="재고관리_stock_history")

app_name = '재고관리'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),

    path('db-field-재고관리_stock_View/', views_db_field.DB_Field_재고관리_STOCK_View.as_view() ),
    # path('db-field-재고관리_도면정보table_View/', views_db_field.DB_Field_재고관리_도면정보Table_Body_View.as_view() ),
    # path('db-field-재고관리_spg_table_View/', views_db_field.DB_Field_재고관리_SPG_Table_View.as_view() ),

]       