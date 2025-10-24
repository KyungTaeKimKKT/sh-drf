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
router.register(r'NCR관리', views.NCR_ViewSet, basename="NCR관리자")
router.register(r'NCR등록', views.NCR_등록_ViewSet, basename="NCR등록")
router.register(r'NCR배포', views.NCR_배포_ViewSet, basename="NCR배포")

# router.register(r'CS관리', views.CS_Manage_ViewSet, basename="CS관리")
# router.register(r'CS등록', views.CS_등록_ViewSet, basename="CS등록")
# router.register(r'CS활동', views.CS_활동_ViewSet, basename="CS활동")
# router.register(r'CS이력조회', views.CS_고이력조회_ViewSet, basename="CS이력조회")
# router.register(r'CS관리-action', views.Action_ViewSet, basename="cs-action")

router.register(r'CS관리', views.CS_Claim_ViewSet, basename="CS관리")
router.register(r'CS활동', views.CS_Activity_ViewSet, basename="CS활동")
router.register(r'CS활동파일', views.CS_Activity_File_ViewSet, basename="CS활동파일")
router.register(r'CS클레임파일', views.CS_Claim_File_ViewSet, basename="CS-claim파일")

router.register(r'CS클레임등록', views.CS_Claim_등록_ViewSet, basename="CS클레임등록")
router.register(r'CS클레임활동', views.CS_Claim_활동_ViewSet, basename="CS클레임활동")
router.register(r'CS클레임이력조회', views.CS_Claim_이력조회_ViewSet, basename="CS클레임이력조회")
router.register(r'CS클레임_활동이력조회', views.CS_Claim_Activity_ViewSet, basename="CS클레임_활동이력조회")


app_name = '품질경영'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),

    path('db-field-CS_Claim_View/', views_db_field.DB_Field_CS_Claim_View.as_view() ),
    path('db-field-CS_Manage_View/', views_db_field.DB_Field_CS_Manage_View.as_view() ),
    path('db-field-CS_Activity_View/', views_db_field.DB_Field_CS_Activity_View.as_view() ),
    path('db-field-CS_Claim_Activity_View/', views_db_field.DB_Field_CS_Claim_Activity_View.as_view() ),
    path('db-field-CS_Claim_사용자_View/', views_db_field.DB_Field_CS_Claim_사용자_View.as_view() ),
    

]       