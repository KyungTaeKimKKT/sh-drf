"""
URL mappings for the 모니터링 app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'Log-로그인', views.Log_login_ViewSet, basename="Log_login")
router.register(r'Log-사용App', views.Log_사용App_ViewSet, basename="Log-사용App")
router.register(r'사내IP-DB', views.사내IP_ViewSet, basename="사내IP-DB")
router.register(r'사내IP-PING결과', views.사내IP_PING결과_ViewSet, basename="사내IP-PING결과")
router.register(r'사내IP-PING결과_IMAGE', views.사내IP_PING결과_IMAGE_ViewSet, basename='사내IP_PING결과_Image')

router.register(r'ApiAccessLog', views.ApiAccessLog_ViewSet, basename="ApiAccessLog")
router.register(r'ClientAppAccess', views.Client_App_Access_Log_ViewSet, basename="ClientAppAccess")

app_name = '모니터링'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),
    # path('계획관리/', views.생산계획_생성.as_view() ),
    path('동시접속자수/', views.동시접속자수.as_view() ),
    path('server-monitor/', views.Server_Monitor.as_view() ),
    
    # path('출하일관리/', views.생산계획_출하일관리.as_view() ),

]       