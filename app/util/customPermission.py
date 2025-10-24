from rest_framework import permissions
# from .models import 생산계획_사용자_DB



class IS_Admin_Permission(permissions.BasePermission):
    """
    Global permission check for User
    """

    def has_permission(self, request, view):
        return request.user.is_active and request.user.is_admin
        qs = 생산계획_사용자_DB.objects.filter(url__icontains=self.url)
        return  qs.filter(user_pks=request.user).count() > 0 
