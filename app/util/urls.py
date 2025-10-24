"""
URL mappings for the users app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
# router.register(r'users', views.UserViewSet)
# router.register(r'app권한', views.Api_App권한ViewSet)
# router.register(r'app사용자', views.Api_App사용자ViewSet)

app_name = 'util'

urlpatterns = [
    path('', include(router.urls)),

#     path('ocr/', views.OCR.as_view()),
#     path('gtts/', views.gTTS_View.as_view()),
#     path('stt-file/', views.STT_File_View.as_view() ),
]