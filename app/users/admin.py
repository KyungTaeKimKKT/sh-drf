from django.contrib import admin
# from django.contrib.auth.models import Group
from django import forms
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.hashers import make_password
from .models import User
from django.utils.html import format_html
from django.urls import reverse

from util.admin_site_register import admin_site_register

app_name = __package__  # == 'users'


class PasswordChangeForm(forms.Form):
    new_password1 = forms.CharField(label="새 비밀번호", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="확인", widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("비밀번호가 일치하지 않습니다.")
        return cleaned

    def save(self, user):
        from django.contrib.auth.hashers import make_password
        user.password = make_password(self.cleaned_data["new_password1"])
        user.save()
        return user

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_mailid', 'user_성명', '기본조직1','is_admin', 'change_pw_link')
    search_fields = ('user_mailid', 'user_성명')

    def change_pw_link(self, obj):
        url = reverse('admin:user_change_password', args=[obj.pk])
        return format_html('<a class="button" href="{}">비밀번호 변경</a>', url)
    change_pw_link.short_description = "비밀번호 변경"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path(
                '<int:user_id>/change-password/',
                self.admin_site.admin_view(self.change_password),
                name='user_change_password',
            ),
        ]
        return custom + urls

    def change_password(self, request, user_id):
        from django.shortcuts import render, redirect, get_object_or_404
        user = get_object_or_404(User, pk=user_id)
        if request.method == 'POST':
            form = PasswordChangeForm(request.POST)
            if form.is_valid():
                form.save(user)
                self.message_user(request, "비밀번호가 변경되었습니다.")
                return redirect(f'../../{user_id}/change/')
        else:
            form = PasswordChangeForm()
        return render(request, 'admin/change_password.html', {'form': form, 'user': user})

### ✅ 25-10.1 추가 : app의 모든 model을 admin site에 등록합니다.
admin_site_register(app_name)


# class CompanyDBAdmin(admin.ModelAdmin):
#     list_display = ('name', 'address', '협력업종','is_active')
#     # list_display = [field.name for field in CompanyDB._meta.get_fields()]  # 모든 필드를 표시합니다.
#     list_filter = ('협력업종',)
#     search_fields = ('name', '협력업종')
# admin.site.register(CompanyDB, CompanyDBAdmin)  # CompanyDB 모델을 등록합니다.


# class UserAdmin(BaseUserAdmin):
#     form = UserChangeForm
#     add_form = UserCreationForm

# #   https://stackoverflow.com/questions/57341155/set-django-admin-to-display-all-the-columns-of-the-database
#     #list_display = [field.name for field in User._meta.get_fields()]
#     # list_display = User._meta.get_all_field_names() ==> 동작 안됨
#     list_display = ('user_mailid', 'user_성명', 'is_admin')
#     list_filter = ('is_admin',)
#     fieldsets = (
#         (None, {'fields': ('user_mailid', 'password','user_성명','user_직책', 'user_직급')}),
#         ('조직정보', {'fields': ('기본조직1','기본조직2','기본조직3')}),
#         ('Permissions', {'fields': ('is_admin','is_active', 'is_mbo_조회자','is_mbo_사용자','is_mbo_관리자',
#                                     'is_일일보고_조회자', 'is_일일보고_사용자', 'is_일일보고_관리자',
#                                     'is_디자인의뢰_조회자','is_디자인의뢰_의뢰자','is_디자인의뢰_접수자','is_디자인의뢰_완료자','is_디자인의뢰_관리자',
#                                     'is_디자인의뢰_대시보드_영업','is_디자인의뢰_대시보드_디자인',
#                                     'is_망관리_조회자', 'is_망관리_사용자','is_망관리_관리자',
#                                     )}),
#     )
    
#     add_fieldsets = (
#         (None, {'fields': ('user_mailid', 'password1','password2','user_성명','user_직책', 'user_직급')}),
#         ('조직정보', {'fields': ('기본조직1','기본조직2','기본조직3')}),
#         ('Permissions', {'fields': ('is_admin','is_active', 'is_mbo_조회자','is_mbo_사용자','is_mbo_관리자',
#                                     'is_일일보고_조회자', 'is_일일보고_사용자', 'is_일일보고_관리자',
#                                     'is_디자인의뢰_조회자','is_디자인의뢰_의뢰자','is_디자인의뢰_접수자','is_디자인의뢰_완료자','is_디자인의뢰_관리자',
#                                     'is_디자인의뢰_대시보드_영업','is_디자인의뢰_대시보드_디자인',
#                                     'is_망관리_조회자', 'is_망관리_사용자','is_망관리_관리자',
#                                     )}),
#     )

#     search_fields = ('user_mailid',)
#     ordering = ('user_mailid',)
#     filter_horizontal = ()


# admin.site.register(User, UserAdmin)
# admin.site.unregister(Group)

# ##  https://medium.datadriveninvestor.com/monitoring-user-actions-with-logentry-in-django-admin-8c9fbaa3f442
# @admin.register(LogEntry)
# class LogEntryAdmin(admin.ModelAdmin):
#     date_hierarchy = 'action_time'

#     list_filter = [
#         'user',
#         'content_type',
#         'action_flag'
#     ]

#     # when searching the user will be able to search in both object_repr and change_message
#     search_fields = [
#         'object_repr',
#         'change_message'
#     ]

#     list_display = [
#         'action_time',
#         'user',
#         'content_type',
#         'action_flag',
#     ]
    # def has_add_permission(self, request):
    #     return False

    # def has_change_permission(self, request, obj=None):
    #     return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    # def has_view_permission(self, request, obj=None):
    #     return request.user.is_admin

    # def object_link(self, obj):
    #     if obj.action_flag == DELETION:
    #         link = escape(obj.object_repr)
    #     else:
    #         ct = obj.content_type
    #         link = '<a href="%s">%s</a>' % (
    #             reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id]),
    #             escape(obj.object_repr),
    #         )
    #     return mark_safe(link)
    # object_link.admin_order_field = "object_repr"
    # object_link.short_description = "object"
################################################


