from rest_framework.views import APIView
from urllib.parse import urlencode
from django.core.cache import cache
from rest_framework.response import Response
from util.base_model_viewset import DBViewPermissionMixin

import util.cache_manager as Cache_Manager

import time

class APICacheMixin:
    use_cache: bool = True
    cache_timeout: int = 60 * 1  # 1시간

    def get_cache_key(self, request, *args, **kwargs):
        path = request.path
        query_string = urlencode(sorted(request.query_params.items()))
        cache_key = f"{self.__class__.__name__}:{path}:{query_string}"
        return cache_key

    def get(self, request, *args, **kwargs):
        print ( "get 호출" )
        start_time = time.time()
        if self.use_cache:
            cache_key = Cache_Manager.get_cache_key(request.get_full_path())
            cached_data = Cache_Manager.get_cache(cache_key)
            if cached_data:
                print("cache hit")
                return Response(cached_data)

            response_data = self.handle_get(request, *args, **kwargs)  # 실제 데이터 처리 함수
            print ( response_data, type(response_data) )
            if response_data:
                Cache_Manager.set_cache(cache_key, response_data, timeout=self.cache_timeout)
            end_time = time.time()
            print ( f"DB 조회 시간: {int((end_time - start_time) * 1000)} msec" )
            return Response(response_data)
        else:
            end_time = time.time()
            print ( f"DB 조회 시간: {int((end_time - start_time) * 1000)} msec" )
            return Response(self.handle_get(request, *args, **kwargs))

    def handle_get(self, request, *args, **kwargs):
        """
        반드시 상속한 클래스에서 override 해야 함
        """
        raise NotImplementedError("handle_get() must be overridden.")
    

class BaseAPIView(APICacheMixin, DBViewPermissionMixin, APIView):
    pass