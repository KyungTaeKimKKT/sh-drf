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


router.register(r'CS관리', views.CS_Claim_ViewSet, basename="CS관리")
# router.register(r'CS활동', views.CS_Activity_ViewSet, basename="CS활동")
# router.register(r'CS활동파일', views.CS_Activity_File_ViewSet, basename="CS활동파일")
# router.register(r'CS클레임파일', views.CS_Claim_File_ViewSet, basename="CS-claim파일")

router.register(r'CS클레임등록', views.CS_Claim_등록_ViewSet, basename="CS클레임등록")
router.register(r'CS클레임활동', views.CS_Claim_활동_ViewSet, basename="CS클레임활동")
# router.register(r'CS클레임이력조회', views.CS_Claim_이력조회_ViewSet, basename="CS클레임이력조회")
# router.register(r'CS클레임_활동이력조회', views.CS_Claim_Activity_ViewSet, basename="CS클레임_활동이력조회")


router.register(r'CS-Activity', views.CS_Activity_ViewSet, basename="CS-Activity")

app_name = 'CS_V2'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),

    path('마이그레이션/', views.Migrate_old_to_new_APIView.as_view() ),


]       