"""
Serializers for 일일보고
"""
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import serializers
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5
from rest_framework.fields import CurrentUserDefault

from datetime import datetime, date,time, timedelta
import datetime as dt
import time

from . import models as 재고관리_models

from 생산관리 import serializers as 생산관리_serializers


class Warehouse_Serializer(serializers.ModelSerializer):
    class Meta:
        model = 재고관리_models.Warehouse
        fields = '__all__'

class Stock_Serializer(serializers.ModelSerializer):
    # 생산관리_제품완료_fk = 생산관리_serializers.생산관리_제품완료_Serializer(read_only=True) 
    # 창고_fk = Warehouse_Serializer(read_only=True) 

    class Meta:
        model = 재고관리_models.Stock
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        ### 1. 제품완료
        if instance.생산관리_제품완료_fk:
            _data = 생산관리_serializers.생산관리_제품완료_Serializer(instance.생산관리_제품완료_fk).data 
            _data.pop('id') # id 제거
            representation.update(_data )
        ### 2. 창고
        if instance.창고_fk:
            _data = Warehouse_Serializer(instance.창고_fk).data 
            _data.pop('id') # id 제거
            representation.update(_data )

        ### 3. 생산지시_process_fk ==>  출하처 
        if ( _확정Branch := instance.생산관리_제품완료_fk.확정Branch_fk ):
            _생지Process = _확정Branch.생산지시_process_fk
            representation['생지_출하처'] = _생지Process.출하처

        ### 4. 출고처
        if instance.출고처_fk:
            representation['출고처'] = instance.출고처_fk.판금처

        return representation

class StockHistory_Serializer(serializers.ModelSerializer):
    class Meta:
        model = 재고관리_models.StockHistory
        fields = '__all__'  



