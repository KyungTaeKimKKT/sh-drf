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
from . import models
from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일
from elevator_info.serializers import Elevator_Summary_WO설치일_Serializer

from util.serializer_for_m2m import Serializer_m2m

class 결재내용_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.결재내용
        fields ='__all__'
        read_only_fields = ['id'] 


class 의장도_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.의장도
        fields ='__all__'
        read_only_fields = ['id'] 



class 첨부file_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.첨부file
        fields = '__all__'
        read_only_fields = ['id'] 

class Rendering_file_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.Rendering_file
        fields = '__all__'
        read_only_fields = ['id'] 

class Process_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.Process
        fields = '__all__'
        read_only_fields = ['id'] 

class 작업지침_Serializer(serializers.ModelSerializer,  Serializer_m2m):
    class Meta:
        model = models.작업지침
        fields = '__all__'
        read_only_fields = ['id'] 
        validators = []  # Remove a default "unique together" constraint.

    def to_representation(self, instance: models.작업지침 ):
        data = super().to_representation(instance)      

        data['요청자'] = instance.작성자_fk.user_성명 if instance.작성자_fk else ''
        data['첨부파일'] = instance.첨부file_fks.count()
        data['대표Render'] = bool(instance.Rendering)
        data['Rendering_URL'] = instance.Rendering.file.url if bool(instance.Rendering) else ''
        # data['완료자'] = instance.완료자_fk.user_성명 if instance.완료자_fk else ''
        # data['완료파일'] = instance.완료file_fks.count()
        data['첨부파일_URL'] = [ _inst.file.url for _inst in instance.첨부file_fks.all() ]
        # data['완료파일_URL'] = [ _inst.file.url for _inst in instance.완료file_fks.all() ]
        data['상세의장수'] = len(set(
                                        ''.join(proc.상세Process.split()) # 모든 공백 문자 제거
                                        for proc in instance.process_fks.all()
                                        if '해당사항' not in ''.join(proc.상세Process.split())  # 공백이 제거된 상태로 비교
                                    ))
        data['의장도_수'] = instance.의장도_fks.count()
        data['영업담당자'] = instance.영업담당자_fk.user_성명 if instance.영업담당자_fk else ''
        data['작성자'] = instance.작성자_fk.user_성명 if instance.작성자_fk else ''
        # data['의장도_URL'] =  [ _inst.file.url for _inst in instance.의장도_fks.all() ]

        ### foreing key로 request 함.
        # if instance.el_info_fk is not None and instance.el_info_fk.id > 0:
        #     data['el_info_수량'] =  instance.el_info_fk.수량
        #     data['el_info_운행층수'] = instance.el_info_fk.운행층수
        #     data['el_info_주소'] = instance.el_info_fk.건물주소_찾기용

        # data['요청자'] = 샘플의뢰_Serializer(instance.샘플의뢰_fk).data
        return data



# class 작업지침_결재_Serializer(작업지침_Serializer):

#     def update(self, instance, validated_data):
        
#         if ( self.결재내용_fks ):
#             for 결재obj in self.결재내용_fks:
#                 for __instance in instance.결재내용_fks.all():
#                     print ( 결재obj )
#                     if ( __instance.id == 결재obj['id'] ):
#                         결재obj.pop('id')
#                         for attr, value in 결재obj.items():
#                             setattr( __instance, attr, value)
#                         __instance.save()
#                         break

#         # instance.진행현황 = self._get_진행현황(instance)
#         instance.save()
#         return instance


#     def _get_inputFields(self, instance):
#         print (self.fields)
#         return self.fields
#     # def _get_현장명_fk_full(self, instance):
#     #     return False

#     # def _get_group_의뢰차수(self, instance):
#     #     return Group작업지침.objects.filter(group = instance.id ).count()
    
#     def _get_첨부file수(self, instance):
#         return instance.첨부file_fks.count()
    
#     def _get_진행현황(self, instance):
#         if ( not instance.결재내용_fks.count() ): return '작성중'
        
#         for 결재instance in instance.결재내용_fks.all() :
#             if ( 결재instance.결재결과 is not None ) :
#                 print ( 결재instance.결재결과, not 결재instance.결재결과)
#                 if( not 결재instance.결재결과 ): return '반려'

#         for 결재instance in instance.결재내용_fks.all() :
#             if ( 결재instance.결재결과 is None) : return '진행중'

#         return '완료'        

#     # def _get_접수디자이너_selector(self, instance):
#     #     url = '/디자인관리/디자인관리_완료.html'
#     #     obj = Api_App권한.objects.get(url=url)
#     #     sel = ['None']
#     #     for userObj in obj.user_pks.all():
#     #         if 'admin' not in userObj.user_성명: sel.append(userObj.user_성명)
#     #     return sel
