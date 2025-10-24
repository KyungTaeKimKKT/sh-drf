from rest_framework import serializers
from . import models as RTSP_CAM_models

class AIModelSerializer(serializers.ModelSerializer):
    task_type_choices = serializers.SerializerMethodField()

    class Meta:
        model = RTSP_CAM_models.AIModel
        fields = [ f.name for f in RTSP_CAM_models.AIModel._meta.fields ] + ['task_type_choices']
        read_only_fields = ['id', 'created_at']

    def get_task_type_choices(self, obj=None):
        return [{'value': val, 'display': label} for val, label in RTSP_CAM_models.AIModel.TASK_CHOICES]

class RTSPCameraSettingSerializer(serializers.ModelSerializer):

    detection_model = serializers.PrimaryKeyRelatedField(
        queryset=RTSP_CAM_models.AIModel.objects.all() , 
        required=False, allow_null=True,
        help_text="감지 모델 선택"
    )
    recognition_model = serializers.PrimaryKeyRelatedField(
        queryset=RTSP_CAM_models.AIModel.objects.all() , 
        required=False, allow_null=True,
        help_text="인식 모델 선택"
    )

    detection_model_data = serializers.SerializerMethodField()
    recognition_model_data = serializers.SerializerMethodField()

    class Meta:
        model = RTSP_CAM_models.RTSPCameraSetting
        fields = [ f.name for f in RTSP_CAM_models.RTSPCameraSetting._meta.fields ] + ['detection_model_data', 'recognition_model_data']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_detection_model_data(self, obj=None):        
        return AIModelSerializer(obj.detection_model).data

    def get_recognition_model_data(self, obj=None):
        return AIModelSerializer(obj.recognition_model).data