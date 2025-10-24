"""
URL mappings for the 생산지시 app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register(r'관리', views.생산지시_ViewSet, basename="생산지시")
# router.register(r'생산현황/당일계획', views.당일생산계획ViewSet)
# router.register(r'결재', views.생산지시_결재_ViewSet, basename="생산지시_결재")
# router.register(r'결재/결재내용', views.결재내용_ViewSet, basename="생산지시_결재내용")

# router.register(r'진행현황', views.생산지시_진행현황_ViewSet, basename="생산지시_진행현황")
# router.register(r'배포', views.생산지시_배포_ViewSet, basename="생산지시_배포")



app_name = '하이생산'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),

]       