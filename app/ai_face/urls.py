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
router.register(r'user-face', views.UserFaceViewSet, basename="user-face")

app_name = 'ai_face'    #   https://velog.io/@ready2start/Django-redirect

urlpatterns = [
    path('', include(router.urls)),


]       