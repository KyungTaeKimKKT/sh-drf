"""
Serializers for 생산관리
"""
from django.conf import settings
from rest_framework import serializers
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5

from datetime import datetime, date,time, timedelta
import datetime as dt
import time
from django.utils import timezone

from users.models import Api_App권한, User
from . import models

from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일
from elevator_info.serializers import Elevator_Summary_WO설치일_Serializer
from 작업지침.serializers import 작업지침_Serializer
import json
from util.serializer_for_m2m import Serializer_m2m

from  . import models as 영업수주Models




class 영업수주_관리_Serializer(serializers.ModelSerializer):
    일정file = serializers.FileField(required=False)
    금액file = serializers.FileField(required=False)
    class Meta:
        model =  영업수주Models.영업수주_관리
        fields = '__all__'


class 영업수주_일정_Serializer(serializers.ModelSerializer):
    class Meta:
        model =  영업수주Models.영업수주_일정
        fields = '__all__'


class 영업수주_금액_Serializer(serializers.ModelSerializer):
    class Meta:
        model = 영업수주Models.영업수주_금액
        fields = '__all__'


class 자재내역_To_의장_Mapping_Serializer(serializers.ModelSerializer):
    class Meta:
        model = 영업수주Models.자재내역_To_의장_Mapping
        fields = '__all__'