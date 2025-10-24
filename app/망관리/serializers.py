"""
Serializers for Serial
"""
from django.conf import settings
from rest_framework import serializers
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5

from datetime import datetime, date,time, timedelta
import datetime as dt
import time
from django.utils import timezone

from .models import (
    망관리_DB,
    망관리_DB_폐기사유
    # Process, 
    # 작업지침,
    # 결재내용,
    # Group작업지침,
    # 의장도file,
    # 의장도, 
    # Rendering_file,
)
from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일
from elevator_info.serializers import Elevator_Summary_WO설치일_Serializer

from util.serializer_for_m2m import Serializer_m2m

class 망관리_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = 망관리_DB
        fields = '__all__'
        # extra_fields =  ['고객사','job_name','생산형태','제품분류','공정','작업명','소재','치수','계획수량']
        # fields =[f.name for f in model._meta.fields] +extra_fields
        read_only_fields = ['id'] 

    def to_representation(self, instance: 망관리_DB ):
        data = super().to_representation(instance)
        data['file수'] = (1 if str(instance.file1) else 0 )+ (1 if str(instance.file2) else 0 ) 
        return data
