"""
URL mappings for the SCM app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views, views_db_field

router = DefaultRouter()
router.register(r'SCM_제품', views.SCM_제품_ViewSet, basename="SCM_제품")
# router.register(r'warehouse', views.Warehouse_ViewSet, basename="SCM_warehouse")
# router.register(r'stock', views.Stock_ViewSet, basename="SCM_stock")
# router.register(r'stock-history', views.StockHistory_ViewSet, basename="SCM_stock_history")

app_name = 'SCM'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),
    path('db-field-SCM_제품_View/', views_db_field.DB_Field_SCM_제품_View.as_view() ),
    # path('db-field-SCM_stock_View/', views_db_field.DB_Field_SCM_STOCK_View.as_view() ),


]       