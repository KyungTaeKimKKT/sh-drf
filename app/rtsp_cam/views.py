from shapi.view_common_import import *

from . import serializers, models

import util.cache_manager as Cache_Manager

class AIModelViewSet(BaseModelViewSet):
    APP_INFO = {'div':'rtsp_cam', 'name':'AI_Model'}
    APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
    MODEL = models.AIModel
    queryset = models.AIModel.objects.all()
    serializer_class = serializers.AIModelSerializer

    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ["is_active", "task_type"] 

    search_fields = ['name', 'version']
    ordering_fields = ['name', 'version']
    ordering = ['name', 'version']

    use_cache = False
    cache_base = 'AIModel'
    cache_timeout = 60*60*1

    @action(detail=False, methods=['get'], url_path='template')
    def template(self, request, *args, **kwargs):
        """ 템플릿 생성 """
        data = self.get_template_data()
        return Response(status=status.HTTP_200_OK, data= data )


class RTSPCameraSettingViewSet(BaseModelViewSet):
    APP_INFO = {'div':'rtsp_cam', 'name':'RTSPCameraSetting'}
    APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
    MODEL = models.RTSPCameraSetting
    queryset = models.RTSPCameraSetting.objects.all()
    serializer_class = serializers.RTSPCameraSettingSerializer

    filterset_fields = ["is_active", "url"] 
    
    search_fields = ['name', 'url']
    ordering_fields = ['name', 'url']
    ordering = ['name', 'url']

    use_cache = False
    cache_base = 'RTSPCameraSetting'
    cache_timeout = 60*60*1

    def _perform_create(self, serializer):
        serializer.save()
        self.invalidate_cache()
        #### 왜냐면, self.invalidate_cache() 는 DRF:{cache_base} 로 캐시를 지우기 때문에, 이 경우는 직접 캐시를 지워줘야 함.
        return serializer.data
    
    def _perform_update(self, serializer):
        serializer.save()
        self.invalidate_cache()
        return serializer.data
    
    def _perform_destroy(self, instance):
        instance.delete()
        self.invalidate_cache()

    @action(detail=False, methods=['get'], url_path='list_alarm_panel')
    def list_alarm_panel(self, request, *args, **kwargs):
        """ 알람 패널 목록 """
        urls_param = request.query_params.get('urls', '')
        urls_list = list(filter(None, urls_param.split(','))) or ['192.168.14.114', '192.168.14.115']
        print(urls_list)
        qs = self.MODEL.objects.filter(is_active=True, url__in=urls_list )
        print(qs)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


    # def retrieve(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     cache_key = f"{self.cache_base}:{instance.url}"
    #     cached_data = Cache_Manager.get_cache(cache_key)
    #     if cached_data:
    #         return Response(cached_data)
    #     serializer = self.get_serializer(instance)
    #     return Response(serializer.data)

    

    @action(detail=True, methods=['patch'], url_path='disconnect_model', parser_classes=[JSONParser])
    def disconnect_model(self, request, *args, **kwargs):
        """ 모델 연결 해제 """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.invalidate_cache()
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    