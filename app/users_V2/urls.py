"""
URL mappings for the users app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
# router.register(r'users', views.UserViewSet)
# router.register(r'users-관리', views.User관리_ViewSet )
# router.register(r'app권한-개발자', views.Api_App개발자_ViewSet)
# router.register(r'app권한', views.Api_App권한ViewSet)
# # router.register(r'app권한-사용자별-권한', views.Api_App사용자별권한_ViewSet)

# router.register(r'error-log', views.ErrorLog_ViewSet)
# router.register(r'app권한-사용자-m2m', views.Api_App권한_User_M2M_ViewSet)

# router.register(r'app권한-사용자-m2m-snapshot', views.App권한_User_M2M_Snapshot_ViewSet)
# router.register(r'company', views.CompanyDBViewSet)

app_name = 'users_V2'

urlpatterns = [
    path('', include(router.urls)),
    ### ✅ 25-7.10 추가 : 부서 관리
    path('department-migration/', views.DepartmentMigrationAPIView.as_view(), name='department-migration'),
    path('user-extension-migration/', views.UserExtensionMigrationAPIView.as_view(), name='user-extension-migration'),
    # path('user-info-by-requestUser/', views.User_Info.as_view() ),

    # path('user-password-change/', views.PasswordChangeView.as_view() ),
    # path('reset-user-password/', views.reset_user_password, name='reset-user-password' ),

    # path('connection-to-no-auth/', views.ConnectionResponse_NoAuth.as_view()),
    # path('connection-to-auth/', views.ConnectionResponse_Auth.as_view()),

    # path('app권한-사용자별-apiview/', views.Api_App권한_사용자별_Api_View.as_view()),
    # ### ✅ 25-7.4 추가 : APP에 관리자 권한 추가
    # path('app권한-admin-check/', views.Api_App권한_Admin_Check_Api_View.as_view()),
]