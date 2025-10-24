from rest_framework import permissions
from .models import 생산계획_사용자_DB



class 당일생산계획_Permission(permissions.BasePermission):
    """
    Global permission check for User
    """
    url = '/일일보고/당일생산계획.html'

    def has_permission(self, request, view):
        qs = 생산계획_사용자_DB.objects.filter(url__icontains=self.url)
        return  qs.filter(user_pks=request.user).count() > 0 

