"""
Serializers for CS_V2
"""
from django.conf import settings
from rest_framework import serializers
from django.core import serializers as core_serializer
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5

from datetime import datetime, date,time, timedelta
import datetime as dt
import time
from django.utils import timezone

from users.models import Api_App권한, User
import CS_V2.models as models


from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일
from elevator_info.serializers import Elevator_Summary_WO설치일_Serializer
# from 작업지침.serializers import 작업지침_Serializer
import json

### fk 로 modeling
class CS_Claim_Serializer(serializers.ModelSerializer):
    claim_file_수 = serializers.SerializerMethodField(read_only=True)
    activity_수 = serializers.SerializerMethodField(read_only=True)
    claim_files_ids = serializers.SerializerMethodField(read_only=True)
    claim_files_url = serializers.SerializerMethodField(read_only=True)
    activity_files_ids = serializers.SerializerMethodField(read_only=True)
    activity_files_url = serializers.SerializerMethodField(read_only=True)
    activity_file_수 = serializers.SerializerMethodField(read_only=True)

    activity_set = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.CS_Claim
        # fields = '__all__'
        fields = [f.name for f in model._meta.fields] + [ 'claim_file_수', 'activity_수', 'claim_files_ids', 'claim_files_url', 'activity_files_ids', 'activity_files_url', 'activity_file_수', 'activity_set']
        read_only_fields = ['id', 'claim_file_수', 'activity_수', 'claim_files_ids', 'claim_files_url', 
                            'activity_files_ids', 'activity_files_url', 'activity_file_수', 'activity_set']

    def get_activity_set(self, instance):
        return CS_Activity_Serializer(instance.CS_Activity_set.all(), many=True).data

    def get_claim_file_수(self, instance):
        return instance.CS_Claim_File_set.count()

    def get_activity_수(self, instance):
        return instance.CS_Activity_set.count()

    def get_claim_files_ids(self, instance):
        return [file.id for file in instance.CS_Claim_File_set.all()]

    def get_claim_files_url(self, instance):
        return [file.file.url for file in instance.CS_Claim_File_set.all()]

    def get_activity_files_ids(self, instance):
        ids = []
        for activity in instance.CS_Activity_set.all():
            ids.extend(file.id for file in activity.CS_Activity_File_set.all())
        return ids

    def get_activity_files_url(self, instance):
        urls = []
        for activity in instance.CS_Activity_set.all():
            urls.extend(file.file.url for file in activity.CS_Activity_File_set.all())
        return urls

    def get_activity_file_수(self, instance):
        return sum(activity.CS_Activity_File_set.count() for activity in instance.CS_Activity_set.all())

  

class CS_Activity_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.CS_Activity
        fields = [f.name for f in model._meta.fields]
        read_only_fields = ['id']   



class CS_Claim_File_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.CS_Claim_File
        fields = [f.name for f in model._meta.fields]
        read_only_fields = ['id']   

class CS_Activity_File_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.CS_Activity_File
        fields = [f.name for f in model._meta.fields]
        read_only_fields = ['id']   






