"""
Serializers for SCM
"""
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import serializers
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5
from rest_framework.fields import CurrentUserDefault

from datetime import datetime, date,time, timedelta
import datetime as dt
import time

from . import models as SCM_models

from 생산관리 import serializers as 생산관리_serializers


class SCM_제품_Serializer(serializers.ModelSerializer):
    class Meta:
        model = SCM_models.SCM_제품 
        fields = '__all__'

    def to_representation(self, instance: SCM_models.SCM_제품):
        representation = super().to_representation(instance)
        ### 1. 출고처 조회
        if ( 출고처_fk := instance.stock_fk.출고처_fk ):
            representation['출고처_fk'] = 출고처_fk.id
            representation['출고처'] = 출고처_fk.판금처
        ### 2. 제품 정보 : 
        if ( 생산관리_제품완료_fk := instance.stock_fk.생산관리_제품완료_fk ):
            _data = 생산관리_serializers.생산관리_제품완료_Serializer(생산관리_제품완료_fk).data 
            _data.pop('id') # id 제거
            representation.update(_data )
        # 
        return representation
