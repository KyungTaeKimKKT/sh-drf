from django.contrib import admin

from util.admin_site_register import admin_site_register, admin_site_register_external

app_name = __package__  # == '영업mbo'
### ✅ 25-10.1 추가 : app의 모든 model을 admin site에 등록합니다.
admin_site_register(app_name)
