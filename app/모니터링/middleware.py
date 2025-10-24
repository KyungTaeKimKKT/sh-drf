from .models import ApiAccessLog
from django.utils.deprecation import MiddlewareMixin



# class ApiAccessLogMiddleware(MiddlewareMixin):
#     def process_view(self, request, view_func, view_args, view_kwargs):
#         if request.method == 'GET' and request.path.startswith('/api/'):
#             user = request.user if request.user.is_authenticated else None
#             ApiAccessLog.objects.create(
#                 user=user,
#                 method=request.method,
#                 path=request.path,
#                 query_params=request.META.get('QUERY_STRING', '')
#             )
#         return None
    
class ApiAccessLogMiddleware(MiddlewareMixin):
    """ ✅ 25-7.4 추가 
    API 접근 로그 기록
    그런데, jwt 라 'django.contrib.auth.middleware.AuthenticationMiddleware', 
    밑에서도 user는 인식 못함.
    """
    # def process_view(self, request, view_func, view_args, view_kwargs):

    #     user = request.user if request.user.is_authenticated else None
    #     print(f"user: {user} , request.method: {request.method} , request.path: {request.path} , request.META.get('QUERY_STRING', ''): {request.META.get('QUERY_STRING', '')}")
    #     ApiAccessLog.objects.create(
    #         user=user,
    #         method=request.method,
    #         path=request.path,
    #         query_params=request.META.get('QUERY_STRING', '')
    #     )
    #     return None
    
    def process_response(self, request, response):

        user = request.user if request.user.is_authenticated else None
        # print(f"user: {user} , request.method: {request.method} , request.path: {request.path} , request.META.get('QUERY_STRING', ''): {request.META.get('QUERY_STRING', '')}")
        # if user is not None and user.id == 1:
        #     return response
        try:
            ApiAccessLog.objects.create(
                user=user,
                method=request.method,
                path=request.path,
                query_params=request.META.get('QUERY_STRING', ''),
            )
        except Exception as e:
            print(f'[log] ApiAccessLog 저장 실패: {e}')
        return response
    

class DRFApiAccessLogMiddleware(MiddlewareMixin):
    """ 
    DRF 인증 이후 시점: request.user 확정됨
    1.  전역 View Dispatch Hook을 만든다
    2.  middle에서 ✅ 반드시 인증 이후
    """
    def process_template_response(self, request, response):
        # DRF 인증 이후 시점: request.user 확정됨
        print(f"request.user: {request.user} , request.method: {request.method} , request.path: {request.path} , request.META.get('QUERY_STRING', ''): {request.META.get('QUERY_STRING', '')}")
        if hasattr(request, 'user'):
            user = request.user if request.user.is_authenticated else None
            try:
                ApiAccessLog.objects.create(
                    user=user,
                    method=request.method,
                    path=request.path,
                    query_params=request.META.get('QUERY_STRING', ''),
                )
            except Exception as e:
                # 실패는 무시
                print(f'[log] ApiAccessLog 저장 실패: {e}')
        return response