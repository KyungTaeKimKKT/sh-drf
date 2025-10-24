"""
URL mappings for the Serial app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'serial-model', views.SerialDB_ViewSet, basename="serialDB-관리")
router.register(r'serial-history', views.SerialHistory_ViewSet, basename="serialHistory-관리")
# router.register(r'조회-by-barcode', views.SerialDB__조회_by_Barcode_ViewSet, basename='serial-조회')


app_name = 'serial'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),
    # path('fields/', views.작업지침_fields_List.as_view() ),

]       