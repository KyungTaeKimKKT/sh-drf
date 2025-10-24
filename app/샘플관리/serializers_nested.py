"""
Serializers for 샘플관리
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
    샘플의뢰,
    완료file,
    # 결재내용,
    Group작업지침, 
)
# from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일
# from elevator_info.serializers import Summary_WO설치일_Serializer


# class 결재내용_Serializer(serializers.ModelSerializer):
#     성명 = serializers.SerializerMethodField('_get_성명')
#     소요시간 = serializers.SerializerMethodField('_get_소요시간')

#     class Meta:
#         model = 결재내용
#         fields =[f.name for f in 결재내용._meta.fields] +['성명','소요시간']
#         read_only_fields = ['id'] 

#     def _get_성명(self, instance):
#         return instance.결재자.user_성명
    
#     def _get_소요시간(self, instance):
#         end = instance.결재일 if instance.결재결과 is not None else timezone.now()
#         return end - instance.의뢰일


class 첨부file_Serializer(serializers.ModelSerializer):

    class Meta:
        model = 첨부file
        fields =[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 

class 완료file_Serializer(serializers.ModelSerializer):

    class Meta:
        model = 완료file
        fields =[f.name for f in 완료file._meta.fields] 
        read_only_fields = ['id'] 

class Process_Serializer(serializers.ModelSerializer):

    class Meta:
        model = Process
        fields =[f.name for f in Process._meta.fields]
        read_only_fields = ['id'] 

class 샘플의뢰_Serializer(serializers.ModelSerializer):
    # 현장명_fk_full = serializers.SerializerMethodField('_get_현장명_fk_full')
    process_fks = Process_Serializer(many=True, required=False)
    첨부file_fks = 첨부file_Serializer(many=True, required=False)
    # 첨부file수 = serializers.SerializerMethodField('_get_첨부file수')
    완료file_fks = 완료file_Serializer(many=True, required=False)

    # 결재내용_fks = 결재내용_Serializer(many=True, required=False)

    class Meta:
        model = 샘플의뢰
        fields =[f.name for f in 샘플의뢰._meta.fields] + ['process_fks' , '첨부file_fks', '완료file_fks'] 
        read_only_fields = ['id'] 
        validators = []  # Remove a default "unique together" constraint.

    def __init__(self, *args, **kwargs):
        if ( fks:= kwargs.pop('fks', None) ):
            for key, value in fks.items():
                self.__setattr__(key, value)

        super().__init__(*args, **kwargs)


    def create(self, validated_data):
        instance = 샘플의뢰.objects.create(**validated_data)
        self._instanace_fks_manage(instance)

        instance.save()
        return instance

    def update(self, instance, validated_data):
        # print ( "update내 validated-data :  최초 - ", validated_data )
        # print ( '--------------------------------------\n\n\n')

        self._instanace_fks_manage(instance)  
        super().update(instance=instance, 
                       validated_data=self._update_validated_data(instance, validated_data))

        return 샘플의뢰.objects.get(id=instance.id)


    def _update_validated_data(self, instance, validated_data) :
        # validated_data['첨부파일수'] = instance.file_fks.count()
        return validated_data
    
    def _instanace_fks_manage(self, instance:샘플의뢰) ->None:
        ### m2m filed
        if hasattr(self, 'process_fks'):
            if ( self.process_fks):
                # print ( self.process_fks)
                instance.process_fks.clear()
                for process in self.process_fks:
                    instance.process_fks.add (self.process_create_or_update(process))

        self.handle_m2m(instance, '첨부file_fks', 첨부file)
        self.handle_m2m(instance, '완료file_fks', 완료file)

      
    def handle_m2m(self, instance, m2m_field:str, Model) -> None:
        if ( instance_m2m := getattr(instance, m2m_field, None) ) is None: return

        if hasattr( self,  f"{m2m_field}_삭제"):
            if getattr(self, f"{m2m_field}_삭제") :
                instance_m2m.clear()
        
        if hasattr( self, f"{m2m_field}_json"):
            if (m2m_json:=  getattr(self, f"{m2m_field}_json" )):
                 instance_m2m.set( m2m_json )

        if hasattr ( self, m2m_field):
            if (m2m := getattr(self, m2m_field) ) :
                for file in m2m:
                    instance_m2m.add( Model.objects.create(file=file))



    def process_create_or_update(self, process:dict) -> object:
        id = process.pop('id', -1)
        if isinstance(id, int) and id >0:
            Process.objects.filter(id = id).update(**process)
            return Process.objects.get(id=id)
        else :
            return  Process.objects.create(**process)

    def _get_inputFields(self, instance):
        print (self.fields)
        return self.fields
    # def _get_현장명_fk_full(self, instance):
    #     return False

    # def _get_group_의뢰차수(self, instance):
    #     return Group작업지침.objects.filter(group = instance.id ).count()
    
    def _get_첨부file수(self, instance):
        return instance.첨부file_fks.count()
    
    def _get_수량(self, instance):
        수량 = 0
        for process in instance.process_fks.all():
            수량 += process.수량
        return 수량

    def _get_진행현황(self, instance):
        if ( not instance.결재내용_fks.count() ): return '작성중'
        
        for 결재instance in instance.결재내용_fks.all() :
            if ( 결재instance.결재결과 is not None ) :
                
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




# class 샘플결과_Serializer(serializers.ModelSerializer):

#     완료file_fks = 완료file_Serializer(many=True, required=False)
#     완료file수 = serializers.SerializerMethodField('_get_완료file수')
#     # 수량 = serializers.SerializerMethodField(method_name='_get_수량')
#     # 결재내용_fks = 결재내용_Serializer(many=True, required=False)

#     class Meta:
#         model = 샘플결과
#         fields =[f.name for f in 샘플결과._meta.fields]  + ['완료file_fks','완료file수'] 
#         read_only_fields = ['id'] 
#         validators = []  # Remove a default "unique together" constraint.

#     def __init__(self, *args, **kwargs):
#         self.완료file_fks = kwargs.pop('완료file_fks', None)
#         # 결재내용_fks = kwargs.pop('결재내용_fks', [])

#         # https://stackoverflow.com/questions/44717442/this-querydict-instance-is-immutable
#         # if kwargs.get('data'): 
#         #     kwargs['data']._mutable = True
#         #     의뢰파일유지 = kwargs['data'].pop('의뢰파일유지', None)
#         #     현장명_fk = kwargs['data'].pop('현장명_fk', [])
#         super().__init__(*args, **kwargs)

#     def to_representation(self, instance):
#         response = super().to_representation(instance)        
#         response['샘플의뢰_fk'] = 샘플의뢰_Serializer(instance.샘플의뢰_fk).data
#         return response


#     def create(self, validated_data):
#         # print ( "Create내 validated-data :  최초 - ", validated_data )
#         # print ( '--------------------------------------\n\n\n')
        
#         _instance = 샘플결과.objects.create(**validated_data)
#         print ( validated_data['샘플의뢰_fk'])
#         print (len(self.완료file_fks) )
#         print ( self._get_수량( validated_data['샘플의뢰_fk'] ))
 
#         if ( self.완료file_fks):
#             if ( len(self.완료file_fks) ==  self._get_수량( validated_data['샘플의뢰_fk'] ) ):
#                 _instance.is_완료 = True
#                 _instance.완료일 = datetime.now()
#                 _instance.save()

#             for file in self.완료file_fks:
#                 _instance.완료file_fks.add( 완료file.objects.create(file=file) )
        
#         return _instance

#     def update(self, instance, validated_data):
#         # print ( "update내 validated-data :  최초 - ", validated_data )
#         # print ( '--------------------------------------\n\n\n')

#         super().update(instance=instance, validated_data=validated_data)
        
#         if ( self.process_fks):
#             instance.process_fks.clear()
#             for process in self.process_fks:
#                 if ( process['id'] == 'new' ) :  # process : dict
#                     process.pop('id','')
#                     instance.process_fks.add( Process.objects.create( **process ) )
#                 else :
#                     process_instance = Process.objects.get( id = process['id'] )
#                     for k, v in process.items():
#                         setattr ( process_instance, k, v)
#                     process_instance.save()
#                     instance.process_fks.add(process_instance )  

#         if ( self.첨부file_fks):
#             instance.첨부file_fks.clear()
#             for file in self.첨부file_fks:
#                 instance.첨부file_fks.add( 첨부file.objects.create(file=file) )

#         # # if ( self.결재내용_fks ):
#         # #     instance.결재내용_fks.clear()
#         # #     기안자 = {
#         # #         '결재자' :  self.context.get('request', None).user,
#         # #         '결재결과' : True,
#         # #         '결재의견' : '결재의뢰 합니다.',
#         # #         '결재일' : timezone.now(),
#         # #         '의뢰일' : timezone.now(),
#         # #     }
#         # #     instance.결재내용_fks.add (결재내용.objects.create( **기안자 ) )
#         # #     for 결재자 in  self.결재내용_fks:
#         # #         instance.결재내용_fks.add (결재내용.objects.create(결재자=User.objects.get(id=결재자), 의뢰일= 기안자['의뢰일'] ))

#         # #     instance.진행현황 = self._get_진행현황(instance)
#             instance.save()
#         return 샘플결과.objects.get(id=instance.id)

#     def _get_inputFields(self, instance):
#         print (self.fields)
#         return self.fields
#     # def _get_현장명_fk_full(self, instance):
#     #     return False

#     # def _get_group_의뢰차수(self, instance):
#     #     return Group작업지침.objects.filter(group = instance.id ).count()
    
#     def _get_완료file수(self, instance):
#         return instance.완료file_fks.count()
    
#     def _get_수량(self, instance):
#         수량 = 0
#         for process in instance.process_fks.all():
#             수량 += process.수량
#         return 수량

#     def _get_진행현황(self, instance):
#         if ( not instance.결재내용_fks.count() ): return '작성중'
        
#         for 결재instance in instance.결재내용_fks.all() :
#             if ( 결재instance.결재결과 is not None ) :
                
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

#         instance.진행현황 = self._get_진행현황(instance)
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
