"""
Serializers for 샘플관리
"""
from typing import Optional
from django.conf import settings
from rest_framework import serializers

from datetime import datetime, date,time, timedelta
import datetime as dt
import time
from django.utils import timezone

from users.models import Api_App권한, User
from .models import (
    출하현장_master_DB, 
    
    관리자등록_DB,
    영업mbo_설정DB,
    영업mbo_엑셀등록,
    고객사_DB, 
    구분_DB,
    기여도_DB,
    사용자_DB,
    년간보고_지사_고객사,
    년간보고_지사_구분,
    년간보고_개인별,
    년간보고_달성률_기준 ,
    보고기준_DB,
    신규현장_등록_DB,
    사용자등록_DB ,
)

def get_active_설정() -> Optional[영업mbo_설정DB]:
    """ 영업mob_설정DB에서 ACTIVE INSTANCE GET"""
    qs = 영업mbo_설정DB.objects.filter( is_시작=True,is_완료=False)
    if qs.count() == 0:
        return None
    return qs.latest( 'id' )

class 출하현장_master_DB_Serializer(serializers.ModelSerializer):
    MODEL = 출하현장_master_DB

    class Meta:
        model = 출하현장_master_DB
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 

class 사용자등록_DB_Serializer(serializers.ModelSerializer):
    MODEL = 사용자등록_DB 

    class Meta:
        model = 사용자등록_DB 
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 

    def create(self, validated_data):
        user: User = self.context['request'].user
        validated_data['등록자'] = user
        validated_data['등록자_snapshot'] = user.user_성명
        return super().create(validated_data)


class 신규현장_등록_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = 신규현장_등록_DB
        fields = ['설정_fk','매출_month','매출_year','현장명','금액'] 
        read_only_fields = ['id'] 

    def __init__(self, *args, **kwargs):
        # 'include_금액' 인자가 없거나 False면 금액을 제거
        include_금액 = kwargs.pop('include_금액', False)
        super().__init__(*args, **kwargs)

        if not include_금액:
            self.fields.pop('금액')

class 신규현장_등록_DB_관리자용_Serializer(serializers.ModelSerializer):
    MODEL = 신규현장_등록_DB

    class Meta:
        model = 신규현장_등록_DB
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 

    def to_representation(self, instance: 신규현장_등록_DB):
        data = super().to_representation(instance)
        # print ( self.context['request'].user )

        if instance.admin_input_fk is not None:
            # data['고객사'] = instance.admin_input_fk__고객사
            for name in ['고객사','구분','기여도','비고']:                    
                data[name] = eval( f"instance.admin_input_fk.{name}" )
            if instance.admin_input_fk.등록자 is not None:
                data['등록자_ID'] = instance.admin_input_fk.등록자.id 
                data['등록자_성명'] = instance.admin_input_fk.등록자.user_성명
                data['부서'] = instance.admin_input_fk.등록자.MBO_표시명_부서        
        if not(ID := data.get('admin_input_fk', False)) :
            data['admin_input_fk'] = -1
        return data



class 관리자등록_DB_Serializer(serializers.ModelSerializer):
    MODEL = 관리자등록_DB

    class Meta:
        model = 관리자등록_DB
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 

    def to_representation(self, instance: 관리자등록_DB):
        data = super().to_representation(instance)
        if instance.담당자_fk is not None:
            data['담당자'] = instance.담당자_fk.user_성명            
            data['부서'] = instance.담당자_fk.MBO_표시명_부서
        return data

class 영업mbo_설정DB_Serializer(serializers.ModelSerializer):
    MODEL = 영업mbo_설정DB
    active_설정: Optional[영업mbo_설정DB] = None

    class Meta:
        model = 영업mbo_설정DB
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 

    def to_representation(self, instance: 영업mbo_설정DB):
        data = super().to_representation(instance)
        if self.active_설정 is None:
            self.active_설정 = get_active_설정()
            if self.active_설정 is None:
                return data
            else:
                if instance.id == self.active_설정.id:
                    data['현재_입력자'] = self.get_현재_입력자(instance)
                else:
                    return data
        else:
            data['현재_입력자'] = self.get_현재_입력자(instance)            
            if instance.id == self.active_설정.id:
                data['현재_입력자'] = self.get_현재_입력자(instance)
            else:
                return data
        return data
    
    def get_현재_입력자(self, instance: 영업mbo_설정DB) -> str:
        총_대상자_qs = User.objects.exclude(MBO_표시명_부서='').filter(is_active=True).values('id', 'user_성명', 'MBO_표시명_부서')
        총_대상자 = list(총_대상자_qs)

        현재_입력자_ids = set(
            사용자등록_DB.objects.filter(신규현장_fk__설정_fk=self.active_설정)
            .values_list('등록자', flat=True)
            .distinct()
        )
        print ( 현재_입력자_ids )
        미입력자_리스트 = [
            f"{user['user_성명']}({user['MBO_표시명_부서']})"
            for user in 총_대상자 if user['id'] not in 현재_입력자_ids
        ]

        입력자수 = len(총_대상자) - len(미입력자_리스트)
        총대상자수 = len(총_대상자)
        미입력자_문자열 = ", ".join(미입력자_리스트)

        return f"현재 입력자 {입력자수}/{총대상자수} : 미입력자 {미입력자_문자열}"

        


class 영업mbo_엑셀등록_Serializer(serializers.ModelSerializer):
    MODEL = 영업mbo_엑셀등록

    class Meta:
        model = 영업mbo_엑셀등록
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 


class 고객사_DB_Serializer(serializers.ModelSerializer):
    MODEL = 고객사_DB

    class Meta:
        model = 고객사_DB
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 

class 구분_DB_Serializer(serializers.ModelSerializer):
    MODEL = 구분_DB

    class Meta:
        model = 구분_DB
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 


class 기여도_DB_Serializer(serializers.ModelSerializer):
    MODEL = 기여도_DB

    class Meta:
        model = 기여도_DB
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 

class 사용자_DB_Serializer(serializers.ModelSerializer):
    MODEL = 사용자_DB

    class Meta:
        model = 사용자_DB
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 

class 년간보고_지사_고객사_Serializer(serializers.ModelSerializer):
    MODEL = 년간보고_지사_고객사

    class Meta:
        model = 년간보고_지사_고객사
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 

class 년간보고_지사_구분_Serializer(serializers.ModelSerializer):
    MODEL = 년간보고_지사_구분

    class Meta:
        model = 년간보고_지사_구분
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 


class 년간보고_개인별_Serializer(serializers.ModelSerializer):
    MODEL = 년간보고_개인별

    class Meta:
        model = 년간보고_개인별
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 

class 년간보고_달성률_기준_Serializer(serializers.ModelSerializer):
    MODEL = 년간보고_달성률_기준

    class Meta:
        model = 년간보고_달성률_기준
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 


class 보고기준_DB_Serializer(serializers.ModelSerializer):
    MODEL = 보고기준_DB

    class Meta:
        model = 보고기준_DB
        fields = '__all__'
        # fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 