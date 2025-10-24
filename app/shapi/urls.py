"""
URL configuration for shapi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
# from django.contrib.staticfiles import views
from django.urls import re_path
from django.views.static import serve

# https://django-rest-framework-simplejwt.readthedocs.io/en/latest/getting_started.html#requirements
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from users.views import CustomTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api-auth/jwt/', TokenObtainPairView.as_view(), name='jwt_obtain_pair'),
    path('api-auth/jwt/', CustomTokenObtainPairView.as_view(), name='jwt_obtain_pair'),
    path('api-auth/jwt/refresh/', TokenRefreshView.as_view(), name='jwt_refresh'),

    path('rq/', include('django_rq.urls')),

    path('release/', include('release.urls')),
    path('util/', include('util.urls')),
    path('api/users/', include('users.urls')),
    path('공지요청사항/', include('공지요청사항.urls')),
    path('모니터링/', include('모니터링.urls')), 

    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/',   SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs',),

    path('생산모니터링/', include('생산모니터링.urls') ),
    path('일일보고/', include('일일보고.urls') ),
    path('디자인관리/', include('sale_design_manage_v1.urls') ),
    path('elevator-info/', include('elevator_info.urls')),
    path('샘플관리/', include('샘플관리.urls')),
    path('작업지침/', include('작업지침.urls')),
    path('생산지시서/', include('생산지시.urls')),
    path('생산관리/', include('생산관리.urls')),
    path('serial/', include('serial.urls')),
    path('재고관리/', include('재고관리.urls')),
    path('SCM/', include('SCM.urls')),
    # path('하이생산/', include('하이생산.urls')),

    path('망관리/', include('망관리.urls')),
    path('품질경영/', include('품질경영.urls')),

    path('scraping/', include('scraping.urls')),

    # path('messagebox/', include('messagebox.urls')),
    
    path('모니터링-schedule/', include('모니터링_schedule.urls')),
    
    path('영업mbo/', include('영업mbo.urls')),
    path('HR평가/', include('HR평가.urls')),
    path('차량관리/', include('차량관리.urls')),

    path('영업수주/', include('영업수주.urls')),

    path('config/', include('config.urls')),
    path('scheduler_job/', include('scheduler_job.urls')),

]

V2_URLS = [
    path('api/users_V2/', include('users_V2.urls')),
    path('HR평가_V2/', include('HR평가_V2.urls')),
    path('차량관리_V2/', include('차량관리_V2.urls')),
    path('CS_V2/', include('CS_V2.urls')),

    path('rtsp_cam/', include('rtsp_cam.urls')),
    path('ai_face/', include('ai_face.urls')),
    path('ai-face/', include('ai_face.urls')),

]

urlpatterns += V2_URLS

if settings.DEBUG:
    # urlpatterns += static( settings.MEDIA_URL, document_root=settings.MEDIA_ROOT, )
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root':settings.STATIC_ROOT}),
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT }),
    ]

    # url(r'^static/(?P<path>.*)$', views.serve, {'document_root':settings.STATIC_ROOT}),
    # url(r'^media/(?P<path>.*)$', views.serve, {'document_root': settings.MEDIA_ROOT }),