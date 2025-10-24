"""
Serializers for 작업지침
"""
from django.conf import settings
from rest_framework import serializers
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5

from datetime import datetime, date,time, timedelta
import datetime as dt
import time
from django.utils import timezone

from users.models import Api_App권한, User
from .models import (
    첨부file, 
    Process, 
    작업지침,
    결재내용,
    Group작업지침,
    의장도file,
    의장도, 
    Rendering_file,
)
from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일
from elevator_info.serializers import Elevator_Summary_WO설치일_Serializer

from util.serializer_for_m2m import Serializer_m2m

class 결재내용_Serializer(serializers.ModelSerializer):
    성명 = serializers.SerializerMethodField('_get_성명')
    소요시간 = serializers.SerializerMethodField('_get_소요시간')

    class Meta:
        model = 결재내용
        fields =[f.name for f in 결재내용._meta.fields] +['성명','소요시간']
        read_only_fields = ['id'] 

    def _get_성명(self, instance):
        return instance.결재자.user_성명
    
    def _get_소요시간(self, instance):
        end = instance.결재일 if instance.결재결과 is not None else timezone.now()
        return end - instance.의뢰일

class 의장도file_Serializer(serializers.ModelSerializer):
    class Meta:
        model = 의장도file
        fields =[f.name for f in 의장도file._meta.fields] 
        read_only_fields = ['id'] 


class 의장도_Serializer(serializers.ModelSerializer):
    의장도_1_data = serializers.SerializerMethodField(method_name='_get_의장도_1_data')
    의장도_2_data = serializers.SerializerMethodField(method_name='_get_의장도_2_data')
    의장도_3_data = serializers.SerializerMethodField(method_name='_get_의장도_3_data')
    의장도_4_data = serializers.SerializerMethodField(method_name='_get_의장도_4_data')
    의장도_5_data = serializers.SerializerMethodField(method_name='_get_의장도_5_data')
    의장도_6_data = serializers.SerializerMethodField(method_name='_get_의장도_6_data')
    의장도_7_data = serializers.SerializerMethodField(method_name='_get_의장도_7_data')
    의장도_8_data = serializers.SerializerMethodField(method_name='_get_의장도_8_data')

    class Meta:
        model = 의장도
        fields =[f.name for f in 의장도._meta.fields] +['의장도_1_data','의장도_2_data','의장도_3_data','의장도_4_data','의장도_5_data','의장도_6_data','의장도_7_data','의장도_8_data']
        read_only_fields = ['id'] 

    def _get_의장도_1_data(self, instance):
        return 의장도file_Serializer(instance.의장도_1, many=False).data
    def _get_의장도_2_data(self, instance):
        return 의장도file_Serializer(instance.의장도_2, many=False).data
    def _get_의장도_3_data(self, instance):
        return 의장도file_Serializer(instance.의장도_3, many=False).data
    def _get_의장도_4_data(self, instance):
        return 의장도file_Serializer(instance.의장도_4, many=False).data
    def _get_의장도_5_data(self, instance):
        return 의장도file_Serializer(instance.의장도_5, many=False).data
    def _get_의장도_6_data(self, instance):
        return 의장도file_Serializer(instance.의장도_6, many=False).data
    def _get_의장도_7_data(self, instance):
        return 의장도file_Serializer(instance.의장도_7, many=False).data
    def _get_의장도_8_data(self, instance):
        return 의장도file_Serializer(instance.의장도_8, many=False).data


class 첨부file_Serializer(serializers.ModelSerializer):

    class Meta:
        model = 첨부file
        fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 

class Rendering_file_Serializer(serializers.ModelSerializer):

    class Meta:
        model = Rendering_file
        fields =[f.name for f in Rendering_file._meta.fields] 
        read_only_fields = ['id'] 

class Process_Serializer(serializers.ModelSerializer):

    class Meta:
        model = Process
        fields =[f.name for f in Process._meta.fields]
        read_only_fields = ['id'] 

class 작업지침_Serializer(serializers.ModelSerializer,  Serializer_m2m):
    process_fks = Process_Serializer(many=True, required=False)
    첨부file_fks = 첨부file_Serializer(many=True, required=False)
    첨부file수 = serializers.SerializerMethodField('_get_첨부file수')
    결재내용_fks = 결재내용_Serializer(many=True, required=False)
    el_info_data = serializers.SerializerMethodField (method_name ='_get_el_info_data' )
    rendering_data = serializers.SerializerMethodField(method_name='_get_rendering_data')
    의장도_fk_datas = serializers.SerializerMethodField(method_name='_get_의장도_fk_datas')

    class Meta:
        model = 작업지침
        fields =[f.name for f in 작업지침._meta.fields] + ['process_fks' , '첨부file_fks','첨부file수', '결재내용_fks','el_info_data','rendering_data', '의장도_fk_datas'] 
        read_only_fields = ['id'] 
        validators = []  # Remove a default "unique together" constraint.

    def _get_el_info_data(self, instance):
        return Summary_WO설치일_Serializer(instance.el_info_fk, many=False).data
    
    def _get_의장도_fk_datas(self, instance):
        return 의장도_Serializer(instance.의장도_fk, many=False).data

    def _get_rendering_data(self, instance):
        return Rendering_file_Serializer(instance.Rendering, many=False).data

    def __init__(self, *args, **kwargs):
        
        if ( fks:= kwargs.pop('fks', None) ):
            for key, value in fks.items():
                self.__setattr__(key, value)
        self.fks_json = {
            "process_fks" : Process,            
        }
        self.fks_files = {
            "첨부file_fks" : 첨부file,
        }
        self.fk_file = {
            "Rendering_file" : Rendering_file,
        }

        super().__init__(*args, **kwargs)


    def create(self, validated_data):
        instance = 작업지침.objects.create(**validated_data)
        self._instanace_fks_manage(instance)
        instance.save()
        return instance
    
    def update(self, instance:작업지침, validated_data):
        self._instanace_fks_manage(instance)  
        super().update(instance=instance, 
                       validated_data=self._update_validated_data(instance, validated_data))

        ### 😀ECO 배포시 처리
        if (instance.진행현황 == '배포') and instance.Rev > 1:
            prev작지 = instance.prev_작지
            prev작지.is_적용 = False
            prev작지.진행현황 = 'ECO UP'
            prev작지.save()

        # instance.진행현황 = self._get_진행현황(instance)
        instance.save()
        return 작업지침.objects.get(id=instance.id)

    # def process_create_or_update(self, process:dict={} ) -> object:
    #     id = process.pop('id', -1)
    #     if isinstance(id, int) and id >0:
    #         Process.objects.filter(id = id).update(**process)
    #         return Process.objects.get(id=id)
    #     else :
    #         return  Process.objects.create(**process)
        
    # def _instanace_fks_manage(self, instance:작업지침) ->None:
    #     ### foreign key
    #     if self.Rendering:
    #         instance.Rendering = Rendering_file.objects.create(file=self.Rendering) 

    #     ### m2m filed

    #     if ( self.process_fks):
    #         instance.process_fks.clear()
    #         for process in self.process_fks:
    #             instance.process_fks.add ( self.process_create_or_update(process) )

    #     instance.첨부file_fks.set(self.첨부file_fks_json)
    #     if ( self.첨부file_fks):
    #         for file in self.첨부file_fks:
    #             instance.첨부file_fks.add( 첨부file.objects.create(file=file) )
        
    #     if ( self.의장도file_fks):
    #         for file in self.의장도file_fks:
    #             instance.의장도file_fks.add( 의장도file.objects.create(file=file) )

    #     if ( self.el_info_fks ):
    #         instance.el_info_fks.set(self.el_info_fks)    


    def _get_inputFields(self, instance):
        print (self.fields)
        return self.fields

    
    def _get_첨부file수(self, instance):
        return instance.첨부file_fks.count()
    
    def _get_진행현황(self, instance):
        if ( not instance.결재내용_fks.count() ): return '작성중'
        
        for 결재instance in instance.결재내용_fks.all() :
            if ( 결재instance.결재결과 is not None ) :
                
                if( not 결재instance.결재결과 ): return '반려'

        for 결재instance in instance.결재내용_fks.all() :
            if ( 결재instance.결재결과 is None) : return '진행중'

        return '완료'        





class 작업지침_결재_Serializer(작업지침_Serializer):

    def update(self, instance, validated_data):
        
        if ( self.결재내용_fks ):
            for 결재obj in self.결재내용_fks:
                for __instance in instance.결재내용_fks.all():
                    print ( 결재obj )
                    if ( __instance.id == 결재obj['id'] ):
                        결재obj.pop('id')
                        for attr, value in 결재obj.items():
                            setattr( __instance, attr, value)
                        __instance.save()
                        break

        # instance.진행현황 = self._get_진행현황(instance)
        instance.save()
        return instance


    def _get_inputFields(self, instance):
        print (self.fields)
        return self.fields
    # def _get_현장명_fk_full(self, instance):
    #     return False

    # def _get_group_의뢰차수(self, instance):
    #     return Group작업지침.objects.filter(group = instance.id ).count()
    
    def _get_첨부file수(self, instance):
        return instance.첨부file_fks.count()
    
    def _get_진행현황(self, instance):
        if ( not instance.결재내용_fks.count() ): return '작성중'
        
        for 결재instance in instance.결재내용_fks.all() :
            if ( 결재instance.결재결과 is not None ) :
                print ( 결재instance.결재결과, not 결재instance.결재결과)
                if( not 결재instance.결재결과 ): return '반려'

        for 결재instance in instance.결재내용_fks.all() :
            if ( 결재instance.결재결과 is None) : return '진행중'

        return '완료'        

    # def _get_접수디자이너_selector(self, instance):
    #     url = '/디자인관리/디자인관리_완료.html'
    #     obj = Api_App권한.objects.get(url=url)
    #     sel = ['None']
    #     for userObj in obj.user_pks.all():
    #         if 'admin' not in userObj.user_성명: sel.append(userObj.user_성명)
    #     return sel
