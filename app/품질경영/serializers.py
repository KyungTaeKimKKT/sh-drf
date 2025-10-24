"""
Serializers for 생산지시
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
from .models import (
    부적합_file, 
    NCR, 
    품질비용,
    부적합내용,
    CS_Manage,

    Claim_File,
    Action_File,
    Action,
    ### fk 로 modeling
    CS_Claim,
    CS_Activity,
    CS_Claim_File,
    CS_Activity_File,
)


from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일
from elevator_info.serializers import Elevator_Summary_WO설치일_Serializer
# from 작업지침.serializers import 작업지침_Serializer
import json

def model_to_dict_custom(instance):
    model_dict = {}
    # Iterate through the model instance's fields
    for field in instance._meta.fields:
        field_name = field.name
        if ( 'NCR_fk' in field_name) :   field_value = instance.NCR_fk_id
        else :   field_value = getattr(instance, field_name)
        # Convert special types if needed (e.g., datetime to string)
        if hasattr(field_value, 'strftime'):
            field_value = field_value.strftime('%Y-%m-%d %H:%M:%S')
        model_dict[field_name] = field_value
    return model_dict


class 부적합내용_Serializer(serializers.ModelSerializer):
    class Meta:
        model = 부적합내용
        fields =[f.name for f in 부적합내용._meta.fields] 
        read_only_fields = ['id'] 


class 부적합_file_Serializer(serializers.ModelSerializer):

    class Meta:
        model = 부적합_file
        fields =[f.name for f in 부적합_file._meta.fields] 
        read_only_fields = ['id'] 

class NCR_Serializer(serializers.ModelSerializer):
    file_fks = 부적합_file_Serializer(many=True, required=False)
    품질비용_fk =  serializers.SerializerMethodField(method_name='_get품질비용_fk')
    contents_fks = 부적합내용_Serializer(many=True, required=False)
    QCost = serializers.SerializerMethodField(method_name='_get_QCost') 

    class Meta:
        model = NCR
        fields =[f.name for f in NCR._meta.fields] + ['file_fks','품질비용_fk', 'contents_fks','QCost'] 
        read_only_fields = ['id'] 
        validators = []  # Remove a default "unique together" constraint.

    def to_representation(self, instance):
        response = super().to_representation(instance)        
        response['작성자_fk'] = instance.작성자_fk.user_성명
        return response
    

    def __init__(self, *args, **kwargs):
        if ( fks:= kwargs.pop('fks', None) ):
            for key, value in fks.items():
                self.__setattr__(key, value)

        super().__init__(*args, **kwargs)

    def _get_QCost(self, instance):
        try : 
            품질비용instance = 품질비용.objects.get(NCR_fk=instance.id)  
            # print ( model_to_dict_custom( 품질비용instance )  )
            return 품질비용instance.합계
            # return 품질비용_Serializer(품질비용instance).data
        except : 
            return ''
    
    def _get품질비용_fk(self, instance):
        try : 
            품질비용instance = 품질비용.objects.get(NCR_fk=instance.id)  
            # print ( model_to_dict_custom( 품질비용instance )  )
            return model_to_dict_custom( 품질비용instance )                               
            # return 품질비용_Serializer(품질비용instance).data
        except : 
            return ''


    def create(self, validated_data):
        print ( "Create내 validated-data :  최초 - ", validated_data )
        print ( '--------------------------------------\n\n\n')

        # print ( self.도면정보_fks)
        instance = NCR.objects.create(**validated_data)

        self._instanace_fks_manage(instance)

        instance.save()
        return instance

    def update(self, instance, validated_data):
        print ( "update내 validated-data :  최초 - ", validated_data )
        print ( '--------------------------------------\n\n\n')
        self._instanace_fks_manage(instance)  
        super().update(instance=instance, 
                       validated_data=self._update_validated_data(instance, validated_data))

        return NCR.objects.get(id=instance.id)
    

    def _update_validated_data(self, instance, validated_data) :
        validated_data['첨부파일수'] = instance.file_fks.count()
        return validated_data
    
    def 부적합내용_create_or_update(self, 부적합내용dict:dict={} ) -> object:
        id = 부적합내용dict.pop('id', -1)
        if isinstance(id, int) and id >0:
            부적합내용.objects.filter(id = id).update(**부적합내용dict)
            return 부적합내용.objects.get(id=id)
        else :
            return  부적합내용.objects.create(**부적합내용dict)

    def _instanace_fks_manage(self, instance:NCR) ->None:
        ## foreign key        
        if self.품질비용_fk:
            # print ( self.품질비용_fk)
            self.품질비용_fk:dict
            if (ID := self.품질비용_fk.pop('id', -1) ) > 0 :     
                품질비용.objects.filter(id = ID).update(**self.품질비용_fk)
                # _instance.update(**self.품질비용_fk) 
            else:
                # self.품질비용_fk.pop('id')
                self.품질비용_fk['NCR_fk'] = instance
                품질비용.objects.create(**self.품질비용_fk)

        ### m2m filed
        if self.file_fks_삭제:         
            instance.file_fks.clear()
        if hasattr(self, 'file_fks_json'):
            if ( self.file_fks_json):
                instance.file_fks.set(self.file_fks_json)        
        if hasattr(self, 'file_fks'):
            if ( self.file_fks):
                for file in self.file_fks:
                    instance.file_fks.add( 부적합_file.objects.create(file=file) )
        

        if hasattr(self, '부적합내용_fks'):
            if ( self.부적합내용_fks):
                # print ( self.부적합내용_fks)
                instance.contents_fks.clear()
                for 부적합 in self.부적합내용_fks:
                    instance.contents_fks.add (self.부적합내용_create_or_update(부적합))

        # if hasattr(self, '완료file'):
        #     if ( self.완료file):
        #         print ( '완료file: ', self.완료file)
        #         for file in self.완료file:
        #             instance.완료file_fks.add( 완료file.objects.create(file=file) )

        # if hasattr(self, 'el_info_fks'):
        #     if ( self.el_info_fks ):
        #         instance.el_info_fks.set(self.el_info_fks)  

    def _get_inputFields(self, instance):
        print (self.fields)
        return self.fields
    # def _get_현장명_fk_full(self, instance):
    #     return False

    # def _get_group_의뢰차수(self, instance):
    #     return Group생산지시.objects.filter(group = instance.id ).count()
    
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

    # def _get_접수디자이너_selector(self, instance):
    #     url = '/디자인관리/디자인관리_완료.html'
    #     obj = Api_App권한.objects.get(url=url)
    #     sel = ['None']
    #     for userObj in obj.user_pks.all():
    #         if 'admin' not in userObj.user_성명: sel.append(userObj.user_성명)
    #     return sel




class 품질비용_Serializer(serializers.ModelSerializer):

    class Meta:
        model = 품질비용
        fields =[f.name for f in 품질비용._meta.fields]
        read_only_fields = ['id'] 

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['NCR_fk'] = NCR_Serializer(instance.NCR_fk).data
        return response

class Action_File_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Action_File
        fields = '__all__' #[f.name for f in Action_File._meta.fields] 
        read_only_fields = ['id'] 
        validators = []  # Remove a default "unique together" constraint.

class Claim_File_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Claim_File
        fields ='__all__' #[f.name for f in Claim_File._meta.fields] 
        read_only_fields = ['id'] 
        validators = []  # Remove a default "unique together" constraint.


class Action_Serializer(serializers.ModelSerializer):
    action_files = Action_File_Serializer(many=True, required=False)
    
    class Meta:
        model = Action
        fields = '__all__' #[f.name for f in Action._meta.fields]  + ['action_files']
        read_only_fields = ['id'] 
        validators = []  # Remove a default "unique together" constraint.

    # def __init__(self, *args, **kwargs):
    #     if ( fks:= kwargs.pop('fks', None) ):
    #         for key, value in fks.items():
    #             self.__setattr__(key, value)

    #     super().__init__(*args, **kwargs)

    # def create(self, validated_data):
    #     instance = Action.objects.create(**validated_data)

    #     self._instanace_fks_manage(instance)

    #     instance.save()
    #     return instance

    # def update(self, instance, validated_data):
    #     self._instanace_fks_manage(instance)  
    #     super().update(instance=instance, 
    #                    validated_data=self._update_validated_data(instance, validated_data))

    #     return Action.objects.get(id=instance.id)
    
    # def _update_validated_data(self, instance, validated_data) :
    #     # validated_data['첨부파일수'] = instance.file_fks.count()
    #     return validated_data
    
    # def _instanace_fks_manage(self, instance:Action) ->None:
    #     ### m2m filed
    #     # if self.action_files_삭제:         
    #     #     instance.action_files.clear()
    #     # if hasattr(self, 'action_files_json'):
    #     #     if ( self.action_files_json):
    #     #         instance.action_files.set(self.action_files_json)        
    #     if hasattr(self, 'files_fks'):
    #         if ( self.files_fks):
    #             for file in self.files_fks:
    #                 instance.action_files.add( Action_File.objects.create(file=file) )
        



class CS_Manage_Serializer(serializers.ModelSerializer):
    # actions = Action_Serializer(many=True, required=False)
    # claim_files = Claim_File_Serializer(many=True, required=False)

    class Meta:
        model = CS_Manage
        fields = '__all__' #[f.name for f in CS_Manage._meta.fields] + ['actions', 'claim_files'] 
        read_only_fields = ['id'] 
        validators = []  # Remove a default "unique together" constraint.

    def to_representation(self, instance:CS_Manage):
        response = super().to_representation(instance)        
        el : Elevator_Summary_WO설치일|None = instance.el_info_fk
        ### fk       
        response['등록자'] = instance.등록자_fk.user_성명 if instance.등록자_fk else ''
        response['완료자'] = instance.완료자_fk.user_성명 if instance.완료자_fk else ''
        if not instance.현장명:            
            response['현장명'] = el.건물명 if el else ''
        if not instance.현장주소:
            response['현장주소'] = el.건물주소_찾기용 if el else ''
        if not instance.el수량:
            response['el수량'] = el.수량 if el else 0
        if not instance.운행층수:
            response['운행층수'] = el.get_운행층수() if el else 0

        ### m2m filed       
        response['claim_file_수'] = instance.claim_file_fks.count()
        response['action_수'] = instance.action_fks.count()
        

        return response
    

    # def __init__(self, *args, **kwargs):
    #     if ( fks:= kwargs.pop('fks', None) ):
    #         for key, value in fks.items():
    #             self.__setattr__(key, value)

    #     super().__init__(*args, **kwargs)


    # def create(self, validated_data):
    #     print ( "Create내 validated-data :  최초 - ", validated_data )
    #     print ( '--------------------------------------\n\n\n')

    #     # print ( self.도면정보_fks)
    #     instance = CS_Manage.objects.create(**validated_data)

    #     self._instanace_fks_manage(instance)

    #     instance.save()
    #     return instance

    # def update(self, instance, validated_data):
    #     print ( "update내 validated-data :  최초 - ", validated_data )
    #     print ( '--------------------------------------\n\n\n')
    #     self._instanace_fks_manage(instance)  
    #     super().update(instance=instance, 
    #                    validated_data=self._update_validated_data(instance, validated_data))

    #     return CS_Manage.objects.get(id=instance.id)
    

    # def _update_validated_data(self, instance, validated_data) :
    #     return validated_data
    
    # def actions_create_or_update(self, action_dict:dict={} ) -> object:
    #     id = action_dict.pop('id', -1)
    #     if isinstance(id, int) and id >0:
    #         Action.objects.filter(id = id).update(**action_dict)
    #         return Action.objects.get(id=id)
    #     else :
    #         return  Action.objects.create(**action_dict)

    # def _instanace_fks_manage(self, instance:CS_Manage) ->None:
    #     ## foreign key        
    #     # if self.품질비용_fk:
    #     #     # print ( self.품질비용_fk)
    #     #     self.품질비용_fk:dict
    #     #     if (ID := self.품질비용_fk.pop('id', -1) ) > 0 :     
    #     #         품질비용.objects.filter(id = ID).update(**self.품질비용_fk)
    #     #         # _instance.update(**self.품질비용_fk) 
    #     #     else:
    #     #         # self.품질비용_fk.pop('id')
    #     #         self.품질비용_fk['NCR_fk'] = instance
    #     #         품질비용.objects.create(**self.품질비용_fk)

    #     ### m2m filed
    #     if self.actions:
    #         instance.actions.set(self.actions)

    #     if self.claim_files_삭제:         
    #         instance.claim_files.clear()
    #     if hasattr(self, 'claim_files_json'):
    #         if ( self.claim_files_json):
    #             instance.claim_files.set(self.claim_files_json)        
    #     if hasattr(self, 'claim_files'):
    #         if ( self.claim_files):
    #             for file in self.claim_files:
    #                 instance.claim_files.add( Claim_File.objects.create(file=file) )


    # def _get_inputFields(self, instance):
    #     print (self.fields)
    #     return self.fields
    # # def _get_현장명_fk_full(self, instance):
    # #     return False



### fk 로 modeling

class CS_Claim_Serializer(serializers.ModelSerializer):
    # serializerMethodField는 readOny 속성이다. 
    # ===> write 필요시, create, update 에서 처리해야 한다.
    # 등록자 = serializers.SerializerMethodField()
    # 완료자 = serializers.SerializerMethodField()
    # 현장명 = serializers.SerializerMethodField()
    # 현장주소 = serializers.SerializerMethodField()
    # el수량 = serializers.SerializerMethodField()
    # 운행층수 = serializers.SerializerMethodField()
    claim_file_수 = serializers.SerializerMethodField()
    activity_수 = serializers.SerializerMethodField()
    claim_files_ids = serializers.SerializerMethodField()
    claim_files_url = serializers.SerializerMethodField()
    activity_files_ids = serializers.SerializerMethodField()
    activity_files_url = serializers.SerializerMethodField()
    activity_file_수 = serializers.SerializerMethodField()


    class Meta:
        model = CS_Claim
        # fields = '__all__'
        fields = [f.name for f in CS_Claim._meta.fields] + [ 'claim_file_수', 'activity_수', 'claim_files_ids', 'claim_files_url', 'activity_files_ids', 'activity_files_url', 'activity_file_수']
        read_only_fields = ['id', 'claim_file_수', 'activity_수', 'claim_files_ids', 'claim_files_url', 'activity_files_ids', 'activity_files_url', 'activity_file_수']

    def get_등록자(self, instance):
        return instance.등록자_fk.user_성명 if instance.등록자_fk else ''

    def get_완료자(self, instance):
        return instance.완료자_fk.user_성명 if instance.완료자_fk else ''

    def get_현장명(self, instance):
        if instance.현장명:
            return instance.현장명
        el = instance.el_info_fk
        return el.건물명 if el else ''

    def get_현장주소(self, instance):
        if instance.현장주소:
            return instance.현장주소
        el = instance.el_info_fk
        return el.건물주소_찾기용 if el else ''

    def get_el수량(self, instance):
        if instance.el수량:
            return instance.el수량
        el = instance.el_info_fk
        return el.수량 if el else 0

    def get_운행층수(self, instance):
        if instance.운행층수:
            return instance.운행층수
        el = instance.el_info_fk
        return el.get_운행층수() if el else 0

    def get_claim_file_수(self, instance):
        return instance.cs_claim_file_set.count()

    def get_activity_수(self, instance):
        return instance.cs_activity_set.count()

    def get_claim_files_ids(self, instance):
        return [file.id for file in instance.cs_claim_file_set.all()]

    def get_claim_files_url(self, instance):
        return [file.file.url for file in instance.cs_claim_file_set.all()]

    def get_activity_files_ids(self, instance):
        ids = []
        for activity in instance.cs_activity_set.all():
            ids.extend(file.id for file in activity.cs_activity_file_set.all())
        return ids

    def get_activity_files_url(self, instance):
        urls = []
        for activity in instance.cs_activity_set.all():
            urls.extend(file.file.url for file in activity.cs_activity_file_set.all())
        return urls

    def get_activity_file_수(self, instance):
        return sum(activity.cs_activity_file_set.count() for activity in instance.cs_activity_set.all())

    # def to_representation(self, instance:CS_Claim):
    #     response :dict = super().to_representation(instance)        
    #     el : Elevator_Summary_WO설치일|None = instance.el_info_fk
    #     ### fk       
    #     response['등록자'] = instance.등록자_fk.user_성명 if instance.등록자_fk else ''
    #     response['완료자'] = instance.완료자_fk.user_성명 if instance.완료자_fk else ''
    #     if not instance.현장명:            
    #         response['현장명'] = el.건물명 if el else ''
    #     if not instance.현장주소:
    #         response['현장주소'] = el.건물주소_찾기용 if el else ''
    #     if not instance.el수량:
    #         response['el수량'] = el.수량 if el else 0
    #     if not instance.운행층수:
    #         response['운행층수'] = el.get_운행층수() if el else 0

    #     ### FK related field set
    #     response['claim_file_수'] = instance.cs_claim_file_set.count()
    #     response['activity_수'] = instance.cs_activity_set.count()  # 수정된 부분
    #     response['claim_files_ids'] = []
    #     response['claim_files_url'] = []
    #     for file in instance.cs_claim_file_set.all():
    #         response['claim_files_ids'].append(file.id)
    #         response['claim_files_url'].append(file.file.url)

    #     # Claim 인스턴스에서 Activity에 연결된 모든 File 수를 계산
    #     activity_files_count = 0
    #     response['activity_files_ids'] = []
    #     response['activity_files_url'] = []
    #     for activity in instance.cs_activity_set.all():
    #         activity_files_count += activity.cs_activity_file_set.count() 
    #         # activity_files_ids.extend(activity.cs_activity_file_set.values_list('id', flat=True))  # 수정된 부분
    #         for file in activity.cs_activity_file_set.all():
    #             response['activity_files_ids'].append(file.id)
    #             response['activity_files_url'].append(file.file.url)

    #     response['activity_file_수'] = activity_files_count
 
    #     return response

class CS_Claim_Activity_Serializer(serializers.ModelSerializer):
    # activities = serializers.SerializerMethodField()

    class Meta:
        model = CS_Claim
        fields = '__all__'  # CS_Claim의 모든 필드 포함

    def get_activities(self, obj):
        activities = CS_Activity.objects.filter(claim_fk=obj)
        return CS_Activity_Serializer(activities, many=True).data


class CS_Activity_Serializer(serializers.ModelSerializer):
    class Meta:
        model = CS_Activity
        fields = '__all__'
        read_only_fields = ['id']   

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['activity_files_ids'] = []
        response['activity_files_url'] = []
        response['activity_file_수'] = instance.cs_activity_file_set.count()
        for file in instance.cs_activity_file_set.all():
            
            response['activity_files_ids'].append(file.id)
            response['activity_files_url'].append(file.file.url)
        return response 

class CS_Claim_File_Serializer(serializers.ModelSerializer):
    class Meta:
        model = CS_Claim_File
        fields = '__all__'
        read_only_fields = ['id']   

class CS_Activity_File_Serializer(serializers.ModelSerializer):
    class Meta:
        model = CS_Activity_File
        fields = '__all__'
        read_only_fields = ['id']   





