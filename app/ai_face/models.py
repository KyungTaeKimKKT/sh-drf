from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

def upload_to_face(instance, filename):
    return f"ai/faces/{instance.user.user_성명}_{instance.user.user_mailid}/{filename}"

def upload_to_face_augmented(instance, filename):   
    return f"ai/faces/augmented/{instance.user_face.user.user_성명}_{instance.user_face.user.user_mailid}/{filename}"

class UserFace(models.Model):
    """
    User와 1:1 연결된 대표 얼굴 데이터
    - 출입 인식 시 실제 사용되는 embedding 저장
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="face")
    representative_image = models.ImageField(upload_to=upload_to_face)  # 대표 사진 (등록 시 지정)
    embedding = ArrayField(models.FloatField(), blank=True, null=True)  # 최종 평균 embedding
    created_at = models.DateTimeField(auto_now_add=True)



class FaceImage(models.Model):
    """
    등록 시 촬영된 원본/증강 이미지를 모두 저장
    - 나중에 재학습/재평균화 용도로 사용 가능
    """
    user_face = models.ForeignKey(UserFace, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=upload_to_face_augmented)
    embedding = ArrayField(models.FloatField(), blank=True, null=True)  # 해당 이미지의 embedding
    created_at = models.DateTimeField(auto_now_add=True)
    is_증강 = models.BooleanField(default=False)

