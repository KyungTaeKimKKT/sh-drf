"""
Serializers for 일일보고
"""
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import serializers
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5
from rest_framework.fields import CurrentUserDefault
from util.serializer_for_m2m import Serializer_m2m
from datetime import datetime, date,time, timedelta
import datetime as dt
import time
from django.db.models import Sum
from users.models import Api_App권한
from .models import (
    디자인의뢰, 
    의뢰file, 
    완료file,
    Group의뢰,
)
from elevator_info.models import Elevator
from elevator_info.serializers import Elevator_Summary_WO설치일_Serializer

class 의뢰file_Serializer(serializers.ModelSerializer):

    class Meta:
        model = 의뢰file
        fields =[f.name for f in 의뢰file._meta.fields] 
        read_only_fields = ['id'] 

class 완료file_Serializer(serializers.ModelSerializer):

    class Meta:
        model = 완료file
        fields =[f.name for f in 완료file._meta.fields] 
        read_only_fields = ['id'] 


class 디자인의뢰_DB_Serializer(serializers.ModelSerializer, Serializer_m2m):

    # 현장명_fk = Elevator_Summary_WO설치일_Serializer(many=True, required=False)
    # 의뢰file_fks = 의뢰file_Serializer(many=True, required=False)
    # 완료file_fks = 완료file_Serializer(many=True, required=False)

    # 의뢰파일수 = serializers.SerializerMethodField('_get_의뢰파일수')
    # 완료파일수 = serializers.SerializerMethodField('_get_완료파일수')
    # 접수디자이너_selector = serializers.SerializerMethodField('_get_접수디자이너_selector')

    # group_id = serializers.SerializerMethodField('_get_group_id')

    class Meta:
        model = 디자인의뢰
        fields = '__all__'
        # fields =[f.name for f in 디자인의뢰._meta.fields] + ['현장명_fk' , '의뢰file_fks', '완료file_fks','의뢰파일수','접수디자이너_selector', 'group_id'] 
        read_only_fields = ['id'] 
        validators = []  # Remove a default "unique together" constraint.

    def to_representation(self, instance:디자인의뢰):
        data = super().to_representation(instance)
        data['의뢰파일수'] = instance.의뢰file_fks.count()
        data['완료파일수'] = instance.완료file_fks.count()

        el수량, 운행층수 = 0, 0
        if  not bool(instance.el수량) :
            for 현장명 in instance.현장명_fk.all():
                el수량 += 현장명.수량            
        if not bool(instance.운행층수):
            for 현장명 in instance.현장명_fk.all():
                운행층수 += Elevator.objects.filter(건물명=현장명.건물명, 건물주소=현장명.건물주소).aggregate(Sum('운행층수'))['운행층수__sum']
        
        data['el수량'] = instance.el수량 if bool(instance.el수량) else el수량
        data['운행층수'] = instance.운행층수 if bool(instance.운행층수) else 운행층수

        return data

    def __init__(self, *args, **kwargs):
        ####😀 '의뢰file_fks_json' , '의뢰file', '완료file_fks_json' , '완료file', '의장도file_fks' 
        if ( fks:= kwargs.pop('fks', None) ):
            for key, value in fks.items():
                self.__setattr__(key, value)
        
        self.fks_ids = {
            "현장명_fk" : '',            
        }
        self.fks_files = {
            "의뢰file_fks" : 의뢰file,
            '완료file_fks' : 완료file,
        }
        # self.fk_file = {
        #     "Rendering_file" : Rendering_file,
        # }

        super().__init__(*args, **kwargs)


    def create(self, validated_data):
        instance = 디자인의뢰.objects.create(**validated_data)
        self._instanace_fks_manage(instance)

        # if ( self.현장명_fk ):
        #     instance.현장명_fk.set(str(self.현장명_fk).split(',')  )


        super().update(instance=instance, 
                       validated_data=self._update_validated_data(instance, validated_data))

        return 디자인의뢰.objects.get(id=instance.id)

    def update(self, instance, validated_data):
        self._instanace_fks_manage(instance)

        super().update(instance=instance, 
                       validated_data=self._update_validated_data(instance, validated_data))

        return 디자인의뢰.objects.get(id=instance.id)

    def _update_validated_data(self, instance, validated_data) :
        validated_data['첨부파일수'] = instance.의뢰file_fks.count()
        validated_data['완료파일수'] = instance.완료file_fks.count()

        의뢰여부 = validated_data.get('의뢰여부', None)
        접수여부 = validated_data.get('접수여부', None)
        완료여부 = validated_data.get('완료여부', None)

        if 의뢰여부 is not None:
            _instance_Group의뢰, _created = Group의뢰.objects.get_or_create(id=instance.temp_group_id, 현장명= instance.현장명 ) 
            if 의뢰여부 : 
                validated_data['의뢰일'] = datetime.now()
                _instance_Group의뢰.group.add(instance)
                validated_data['temp_group_id'] = None
                validated_data['의뢰차수'] = _instance_Group의뢰.group.count()
            else:
                validated_data['의뢰일'] = None
                _instance_Group의뢰.group.remove(instance)
                validated_data['temp_group_id'] = _instance_Group의뢰.id
                if ( not _instance_Group의뢰.group.count() ): _instance_Group의뢰.delete()

        
        if 접수여부 is not None:
            validated_data['접수일'] = datetime.now() if ( validated_data.get('접수여부', None) == True ) else None
            validated_data['접수디자이너'] = validated_data['접수디자이너']  if ( validated_data.get('접수여부', None) == True ) else None

        if 완료여부 is not None:
            validated_data['완료일'] = datetime.now() if ( validated_data.get('완료여부', None) == True ) else None
            validated_data['완료디자이너'] = validated_data['완료디자이너']  if ( validated_data.get('완료여부',None) == True ) else None

        # instance.save(**validated_data)
        return validated_data

    # def _instanace_fks_manage(self, instance:디자인의뢰) ->None:
    #     ### foreign key
    #     # if self.Rendering:
    #     #     instance.Rendering = Rendering_file.objects.create(file=self.Rendering) 

    #     ### m2m filed
    #     if self.의뢰file_삭제:         
    #         instance.의뢰file_fks.clear()

    #     if hasattr(self, '의뢰file_fks_json'):
    #         if ( self.의뢰file_fks_json):
    #             instance.의뢰file_fks.set(self.의뢰file_fks_json)

    #     if hasattr(self, '의뢰file'):
    #         if ( self.의뢰file):
    #             for file in self.의뢰file:
    #                 instance.의뢰file_fks.add( 의뢰file.objects.create(file=file) )
        
    #     if hasattr(self, '완료file'):
    #         if ( self.완료file):
    #             print ( '완료file: ', self.완료file)
    #             for file in self.완료file:
    #                 instance.완료file_fks.add( 완료file.objects.create(file=file) )

    #     if hasattr(self, 'el_info_fks'):
    #         if ( self.el_info_fks ):
    #             instance.el_info_fks.set(self.el_info_fks)    


    def _get_group_id(self, instance):
        try : 
            obj = Group의뢰.objects.get( group = instance.id)
            return obj.id
        except :
            return None 

    def _get_현장명_fk_full(self, instance):
        return False

    def _get_group_의뢰차수(self, instance):
        return 0
        return Group의뢰.objects.filter(group = instance.id ).count()
    
    def _get_의뢰파일수(self, instance):
        return instance.의뢰file_fks.count()
    
    def _get_완료파일수(self, instance):
        return instance.완료file_fks.count()

    def _get_접수디자이너_selector(self, instance):
        url = '/디자인관리/디자인관리_완료.html'
        obj = Api_App권한.objects.get(url=url)
        sel = ['None']
        for userObj in obj.user_pks.all():
            if 'admin' not in userObj.user_성명: sel.append(userObj.user_성명)
        return sel


class Group의뢰_Serializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(queryset=의뢰file.objects.all(), many=True, required=False )
    # group_fks = 디자인의뢰_DB_Serializer( many=True, required=False )

    class Meta:
        model = Group의뢰
        fields =[f.name for f in Group의뢰._meta.fields] +['group']
        # read_only_fields = ['id'] 


# class 개인_리스트_DB_Serializer(serializers.ModelSerializer):
#     # 등록자_id = 개인_INFO_Serializer(read_only=True )
#     일자list = serializers.SerializerMethodField('_get_일자list')

#     class Meta:
#         model = 개인_리스트_DB
#         # https://stackoverflow.com/questions/64476816/how-to-add-new-serializer-field-along-with-the-all-model-fields
#         # fields = [f.name for f in 개인_리스트_DB._meta.fields] + ['일자list' ] - ['등록자_id',['조직이름_id']]
#         # fields = '__all__'
#         fields = ['id','일자','업무내용','업무주기','소요시간','주요산출물','비고','일자list']
#         read_only_fields = ['id']

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         data['보고자'] = instance.등록자_id.user_fk.user_성명
#         data['조직'] = instance.조직이름_id.조직이름
#         return data

#     def _get_일자list(self, instance):
#         day_list =[]
#         day = datetime.today()
#         delta = timedelta(days=1)
#         while ( len(day_list) <= 2 ):
#             if ( not 휴일_DB.objects.filter( 휴일= day) ): day_list.append(day)
#             day -=delta
#         return sorted(day_list)
    
#     def _get_current_user(self):
#         request = self.context.get('request', None)
#         if request.user == 'AnonymousUser':
#             return 'AnonymousUser' #request.user
#         else :
#             return request.user

#     def _get_등록자_id(self, id, instance):
#         for key, value in id.items():
#             print ( key , ":  ", value )
#             instance.등록자_id = 개인_INFO.objects.get(user_fk=value)

#         # instance.등록자_id.add(개인_INFO.objects.get(user_fk=user_fk))


#     def create(self, validated_data):
#         validated_data['등록자_id'] = 개인_INFO.objects.get(user_fk= self._get_current_user()) 
#         validated_data['조직이름_id'] = 조직_INFO.objects.get( 조직이름 = self._get_current_user().기본조직1) 

#         instance = 개인_리스트_DB.objects.create (**validated_data)
#         return instance
    


# class 조직_리스트_DB_Serializer(serializers.ModelSerializer):
#     # 등록자_id = 개인_INFO_Serializer(read_only=True )
#     일자list = serializers.SerializerMethodField('_get_일자list')
#     is전기등록 = serializers.SerializerMethodField('_get_is전기등록')

#     class Meta:
#         model = ISSUE_리스트_DB
#         fields = ['id','일자','활동현황','세부내용','완료예정일','진척율','유관부서','비고','일자list'] +['is전기등록']
#         read_only_fields = ['id']

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         data['보고자'] = instance.등록자_id.user_fk.user_성명
#         data['조직'] = instance.조직이름_id.조직이름
#         return data

#     def _get_일자list(self, instance):
#         day_list =[]
#         day = datetime.today()
#         delta = timedelta(days=1)
#         while ( len(day_list) <= 2 ):
#             if ( not 휴일_DB.objects.filter( 휴일= day) ): day_list.append(day)
#             day -=delta
#         return sorted(day_list)
    
#     def _get_is전기등록(self, instance):
#         qs = 개인_INFO.objects.filter(user_fk = self._get_current_user(), is_전기사용=True)
#         return qs.count() >0 

#     def _get_current_user(self):
#         request = self.context.get('request', None)
#         if request.user == 'AnonymousUser':
#             return 'AnonymousUser' #request.user
#         else :
#             return request.user

#     def create(self, validated_data):
#         validated_data['등록자_id'] = 개인_INFO.objects.get(user_fk= self._get_current_user()) 
#         validated_data['조직이름_id'] = 조직_INFO.objects.get( 조직이름 = self._get_current_user().기본조직1) 

#         instance = ISSUE_리스트_DB.objects.create (**validated_data)
#         return instance


# class 전기사용량_DB_Serializer(serializers.ModelSerializer):
#     today = serializers.SerializerMethodField('_get_일자')
#     class Meta:
#         model = 전기사용량_DB
#         fields = ['id','등록자','하이전기_file','폴리전기_file','일자'] +['today']
#         read_only_fields = ['id']

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         # data['보고자'] = instance.등록자_id.user_fk.user_성명
#         # data['조직'] = instance.조직이름_id.조직이름
#         return data

#     def _get_일자(self, instance):
#         day_list =[]
#         day = datetime.today()
#         delta = timedelta(days=1)
#         while ( len(day_list) <= 2 ):
#             if ( not 휴일_DB.objects.filter( 휴일= day) ): day_list.append(day)
#             day -=delta
        
#         return sorted(day_list)[1]
    
#     def _get_is전기등록(self, instance):
#         qs = 개인_INFO.objects.filter(user_fk = self._get_current_user(), is_전기사용=True)
#         return qs.count() >0 

#     def _get_current_user(self):
#         request = self.context.get('request', None)
#         if request.user == 'AnonymousUser':
#             return 'AnonymousUser' #request.user
#         else :
#             return request.user

#     def create(self, validated_data):
#         print ( type(self._get_current_user().user_성명),  self._get_current_user().user_성명 )
#         validated_data['등록자'] = self._get_current_user().user_성명
 
#         instance = 전기사용량_DB.objects.create (**validated_data)
#         return instance


