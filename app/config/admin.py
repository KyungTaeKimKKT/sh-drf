from django.contrib import admin, messages
from django.urls import path
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.conf import settings
import redis

from util.admin_site_register import admin_site_register
from 생산지시.admin import app_name
from .models_proxy import RedisCacheAdmin

app_name = __package__  # == 'config'
### ✅ 25-10.1 추가 : app의 모든 model을 admin site에 등록합니다.

class RedisCacheAdminAdmin(admin.ModelAdmin):
    change_list_template = "admin/redis_cache_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("", self.admin_site.admin_view(self.index_view), name="config_rediscacheadmin_changelist"),
            path("clear/", self.admin_site.admin_view(self.clear_cache), name="config_rediscacheadmin_clear"),
        ]
        return custom_urls

    def index_view(self, request):
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB_FOR_CACHE, 
            password=settings.REDIS_PASSWORD,
        )

        try:
            info = r.info()
            keys = r.keys("*")
            data = []
            total_kb = 0
            for key in keys:
                size = r.memory_usage(key)
                size_kb = (size or 0) / 1024
                total_kb += size_kb
                data.append({
                    "key": key.decode(),
                    "size_kb": round(size_kb, 2),
                })
            total_gb = round(total_kb / 1024 / 1024, 3)
        except Exception as e:
            info = {}
            data = []
            total_gb = 0
            messages.error(request, f"Failed to connect Redis: {e}")

        context = {
            "title": "Redis Cache Status",
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "db": settings.REDIS_DB_FOR_CACHE,
            "total_gb": total_gb,
            "data": data,
        }
        return render(request, self.change_list_template, context)

    def clear_cache(self, request):
        try:
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB_FOR_CACHE,
                password=settings.REDIS_PASSWORD,
            )
            r.flushall()
            messages.success(request, "Redis cache cleared.")
        except Exception as e:
            messages.error(request, f"Redis clear failed: {e}")
        return HttpResponseRedirect("../")

admin.site.register(RedisCacheAdmin, RedisCacheAdminAdmin)


admin_site_register(app_name)