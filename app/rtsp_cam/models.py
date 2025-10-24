from unittest import defaultTestLoader
from django.db import models
from datetime import datetime

# Create your models here.
# def upload_to_rtsp_cam(instance: 'RTSPCameraSetting', filename: str) -> str:
#     date_str = datetime.now().strftime('%Y%m%d')
#     return f'rtsp_cam/{instance.url}/{date_str}/{filename}'

def upload_to_ai_model(instance: 'AIModel', filename: str) -> str:
    return f'ai_models/{instance.name}/{instance.task_type}/{instance.version}/{filename}'

class AIModel(models.Model):
    TASK_CHOICES = [
        ("감지", "감지"),
        ("인식", "인식"),
        ("분류", "분류"),
    ]

    name = models.CharField(max_length=100, default="입력하세요")
    version = models.CharField(max_length=20 , default="1.0.0")
    task_type = models.CharField(max_length=20, choices=TASK_CHOICES, default="감지")

    model_file = models.FileField(
        upload_to=upload_to_ai_model,  # MEDIA_ROOT/models/ 에 저장됨
        blank=False,
        null=False
    )

    metrics = models.JSONField(null=True, blank=True, default=dict)  # {"acc":0.98, "f1":0.92}
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    비고 = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("name", "task_type", "version")


class RTSPCameraSetting(models.Model):
    name = models.CharField(max_length=100)           # 예: 설비1_천단위
    url = models.CharField(max_length=500)           ### URL 필드는 스키마(http://, https://, rtsp:// …) 가 반드시 들어가야 합니다
    port = models.IntegerField(default=10500)
    rois = models.JSONField(default=dict)      
    settings = models.JSONField(default=dict) # {"roi_key": {"x":..., "y":..., "w":..., "h":...}}
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    # AI 모델 연결
    detection_model = models.ForeignKey(
        AIModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="cameras_for_detection",
        limit_choices_to={"is_active": True}, 
        ###관리자가 구버전 모델을 is_active=False 로 만들면, 새 카메라 등록 시 선택 불가.(기존 카메라는 영향 없음)
    )
    recognition_model = models.ForeignKey(
        AIModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="cameras_for_recognition",
        limit_choices_to={"is_active": True},
    )