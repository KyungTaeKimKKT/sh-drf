from rest_framework import permissions
from .models import User, Api_App권한

class CustomPermission(permissions.BasePermission):
    """
    Global permission check for User
    """

    def has_permission(self, request, view):
         return Api_App권한.objects.filter(user_pks=request.user).count() > 0