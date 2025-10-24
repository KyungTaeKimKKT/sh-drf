"""
Serializers for User
"""
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import serializers
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5
from rest_framework.fields import CurrentUserDefault

from rest_framework.authtoken.models import Token
from datetime import timedelta, datetime, time

from . import models

from util.utils_func import CustomDecimalField

import logging, traceback
logger = logging.getLogger('users')

# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from rest_framework_simplejwt.views import TokenObtainPairView
# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)
#         return token
        
#     def validate(self, attrs):
#         data = super().validate(attrs)

#         is_dev = attrs.get('is_dev', False)
#         logger.info(f"is_dev: {is_dev}, {type(is_dev)}")
#         logger.info(f" self.user.id == 1: { self.user.id == 1}, is_dev: {is_dev}")
#         # 현재 날짜 가져오기
#         today = datetime.now().date()
        
#         # 토큰 가져오기
#         refresh = self.get_token(self.user)

#         # 조건에 따라 만료 시간 설정
#         if self.user.id == 1 and is_dev:
#             # 7일 후 날짜 계산
#             expiry_date = today + timedelta(days=7)
#         else:
#             # 오늘 날짜 사용
#             expiry_date = today

#         # 해당 날짜의 23:59:59 시간으로 설정
#         end_of_day = datetime.combine(expiry_date, time(23, 59, 59))
        
#         # Unix timestamp로 변환하여 토큰 만료 시간 설정
#         refresh.payload['exp'] = int(end_of_day.timestamp())
        
#         # 응답 데이터 업데이트
#         data['refresh'] = str(refresh)
#         data['access'] = str(refresh.access_token)
#         # 응답에 user_id 추가
#         data['user_info'] = UserSerializer(self.user).data
#         return data


# class CompanyDBSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CompanyDB
#         fields = '__all__'

# class PasswordChangeSerializer(serializers.Serializer):
#     old_password = serializers.CharField(required=True)
#     new_password = serializers.CharField(required=True)
#     confirm_password = serializers.CharField(required=True)

#     def validate(self, data):
#         if data['new_password'] != data['confirm_password']:
#             raise serializers.ValidationError("새 비밀번호가 일치하지 않습니다.")
#         return data


# class UserSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = User
#         exclude = ['password']
#         # fields = '__all__'
#         read_only_fields = ['id']

#     def to_representation(self, instance: User):
#         representation = super().to_representation(instance)
#         if instance.Company_fk:
#             representation['Company_fk'] = instance.Company_fk.id
#             representation['Company'] = instance.Company_fk.name
#         return representation

#     # class Meta:
#     #     model = User
#     #     fields = ['id','user_mailid', 'user_성명','user_직책', 'user_직급', '기본조직1','기본조직2','기본조직3','is_active', 'is_admin']
#     #     # read_only_fields = ['id']
#     #     extra_kwargs = {'user_성명' :{'required': False},
#     #                     'user_직책' :{'required': False},
#     #                     'user_직급' :{'required': False},
#     #                     '기본조직1' :{'required': False},
#     #                     '기본조직2' :{'required': False},
#     #                     '기본조직3' :{'required': False},
#     #                     }


# class Api_App사용자Serializerr(serializers.ModelSerializer):

#     # username = serializers.SerializerMethodField('_get_current_username')
#     # userid    = serializers.SerializerMethodField('_get_current_userid')

#     class Meta:
#         model = Api_App권한
#         fields = '__all__'
#         # fields = ['div','name','url','api_url'] +['username', 'userid']

#     def _get_current_username(self, instance):
#         request = self.context.get('request', None)
#         if request.user == 'AnonymousUser':
#             return 'Anonymous' #request.user
#         else :
#             return request.user.user_성명
        
#     def _get_current_userid(self, instance):
#         request = self.context.get('request', None)
#         if request.user == 'AnonymousUser':
#             return  -1 #request.user
#         else :
#             return  request.user.id

# class Api_App권한_User_M2MSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Api_App권한_User_M2M
#         fields = '__all__'

# class Api_App권한Serializer(serializers.ModelSerializer):
#     user_list = serializers.SerializerMethodField('get_user_relations')
#     user_pks = serializers.SerializerMethodField('get_user_pks')
#     app사용자수 = serializers.SerializerMethodField('_get_app사용자수')
   
#     class Meta:
#         model = Api_App권한
#         fields = [f.name for f in Api_App권한._meta.fields] + ['user_pks', 'user_list', 'app사용자수']
#         extra_kwargs = {
#             'help_page': {'allow_null': True, 'required': False},
#         }

#     # 캐싱을 위한 속성 추가
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._relations_cache = {}
    
#     def _get_relations(self, instance):
#         """관계 데이터를 한 번만 쿼리하고 캐싱하는 헬퍼 메서드"""
#         if instance.id not in self._relations_cache:
#             # id=1인 사용자를 제외한 관계만 가져오기
#             self._relations_cache[instance.id] = list(Api_App권한_User_M2M.objects.filter(
#                 app_권한=instance
#             ).exclude(user_id=1).select_related('user'))
#         return self._relations_cache[instance.id]
    
#     def get_user_pks(self, instance):
#         """앱 권한과 연결된 사용자 ID 목록을 가져오는 메서드 (id=1 제외)"""
#         relations = self._get_relations(instance)
#         return [relation.user_id for relation in relations]
    
#     def get_user_relations(self, instance):
#         """앱 권한과 연결된 사용자 관계 정보를 가져오는 메서드 (id=1 제외)"""
#         relations = self._get_relations(instance)
#         data = Api_App권한_User_M2MSerializer(relations, many=True).data
#         return [{k: v for k, v in item.items() if k != 'app_권한'} for item in data]
    
#     def _get_app사용자수(self, instance):
#         """앱 사용자 수를 계산하는 메서드 (id=1 제외)"""
#         return len(self._get_relations(instance))

#     def create(self, validated_data):
#         user_pks = validated_data.pop('user_pks',[])
#         if not user_pks:
#             user_pks = [1]
#         api_권한 = Api_App권한.objects.create (**validated_data)
#         api_권한.user_pks.set(user_pks )
#         return api_권한
 
#     # https://stackoverflow.com/questions/50654337/django-writable-nested-serializers-update
#     def update(self, instance, validated_data):
#         user_pks = validated_data.pop('user_pks',[])
#         if (user_pks):  instance.user_pks.set(user_pks)
#         # if user_pks is not None:
#         #     instance.user_pks.set(user_pks )
        
#         if 'help_page' in validated_data and validated_data['help_page'] is None:
#             # 파일 삭제
#             instance.help_page.delete(save=False)
#             instance.help_page = None
        
#         return super().update(instance, validated_data)


# class Api_App권한Serializer_for_개인별(serializers.ModelSerializer):
   
#     class Meta:
#         model = Api_App권한
#         fields = ['id', '표시명_구분', '표시명_항목', 'is_Active', 'is_Run' ] 
#         read_only_fields = ['id', '표시명_구분', '표시명_항목', 'is_Active', 'is_Run' ]



# class ErrorLogSerializer(serializers.ModelSerializer):
#     버젼 = CustomDecimalField(max_digits=5, decimal_places=2,  coerce_to_string=False)
#     class Meta:
#         model = ErrorLog
#         fields = '__all__'

#     def to_representation(self, instance):
#         ret = super().to_representation(instance)
#         if instance.user_fk:
#             ret['성명'] = instance.user_fk.user_성명

#         return ret


# class App권한_User_M2M_SnapshotSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = App권한_User_M2M_Snapshot
#         fields = ['id', 'timestamp']
#         read_only_fields = ['id', 'timestamp']
