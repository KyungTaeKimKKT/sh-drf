from rest_framework import permissions
from users.models import User, Api_App권한



class 개인_리스트_DB_전사_Permission(permissions.BasePermission):
    """
    Global permission check for User
    """
    url = '/일일보고/개인전사.html'

    def has_permission(self, request, view):
        qs = Api_App권한.objects.filter(url__icontains=self.url)
        return  qs.filter(user_pks=request.user).count() > 0 


class 개인_리스트_DB_개인_Permission(permissions.BasePermission):
    """
    Global permission check for User
    """
    url = '/일일보고/개인.html'

    def has_permission(self, request, view):
        qs = Api_App권한.objects.filter(url__icontains=self.url)
        # print (type(request.user), request.user )
        # print ( qs.filter(user_pks=request.user).count()>0 )

        return  qs.filter(user_pks=request.user).count() > 0 



class 조직_리스트_DB_전사_Permission(permissions.BasePermission):
    """
    Global permission check for User
    """
    url = '/일일보고/조직전사.html'

    def has_permission(self, request, view):
        qs = Api_App권한.objects.filter(url__icontains=self.url)
        return  qs.filter(user_pks=request.user).count() > 0 


class 조직_리스트_DB_개인_Permission(permissions.BasePermission):
    """
    Global permission check for User
    """
    url = '/일일보고/조직.html'

    def has_permission(self, request, view):
        qs = Api_App권한.objects.filter(url__icontains=self.url)
        return  qs.filter(user_pks=request.user).count() > 0 
    
class 전기사용량_DB_Permission(permissions.BasePermission):
    """
    Global permission check for User
    """
    url = '/일일보고/전기사용량.html'

    def has_permission(self, request, view):
        qs = Api_App권한.objects.filter(url__icontains=self.url)
        return  qs.filter(user_pks=request.user).count() > 0 
    
class 휴일등록_DB_Permission(permissions.BasePermission):
    """
    Global permission check for User
    """
    url = '/일일보고/휴일등록.html'

    def has_permission(self, request, view):
        qs = Api_App권한.objects.filter(url__icontains=self.url)
        return  qs.filter(user_pks=request.user).count() > 0 