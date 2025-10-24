
from rest_framework import serializers
from .models import UserFace, FaceImage
from django.conf import settings
from users.models import User


class FaceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaceImage
        fields = [ f.name for f in FaceImage._meta.fields ]
        read_only_fields = ["id", "created_at"]


class UserFaceSerializer(serializers.ModelSerializer):
    images = FaceImageSerializer(many=True, read_only=True)

    class Meta:
        model = UserFace
        fields = [ f.name for f in UserFace._meta.fields ] + ["images"]
        read_only_fields = ["embedding", "created_at", "images"]


class UserFaceStatusSerializer(serializers.ModelSerializer):
    """ 모든 사용자에 대해서 nested serializer 사용 """
    representative_image = serializers.ImageField(source='face.representative_image', default=None)
    등록여부 = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.DateTimeField(source='face.created_at', default=None)

    images = serializers.SerializerMethodField( read_only=True)

    class Meta:
        model = User
        fields = ["id", "user_성명", "기본조직1", "representative_image", "등록여부", "created_at", "images"]

    def get_등록여부(self, obj:User):
        # face가 없으면 False
        return getattr(obj, 'face', None) and obj.face.embedding is not None

    def get_images(self, obj):
        face = getattr(obj, 'face', None)
        if face is None:
            return []
        qs = FaceImage.objects.filter(user_face=face)
        return FaceImageSerializer(qs, many=True).data