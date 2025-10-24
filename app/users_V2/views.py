"""
Views for the contact APIs
"""
from drf_spectacular.utils import (
	extend_schema_view,
	extend_schema,
	OpenApiParameter,
	OpenApiTypes,
)

from rest_framework import (
	viewsets,
	mixins,
	status,
)
from django.db import transaction
from django.db.models import Prefetch
from django.db.models.signals import post_save, post_delete
from users.signals import Api_App권한_changed

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework.response import Response
# from rest_framework.authentication import TokenAuthentication, SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.http import QueryDict
# from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken

from util.base_model_viewset import BaseModelViewSet

import config.models as Config_models
from util.customfilters import *

from . import serializers, models
from users import models as old_models

import util.utils_func as Util
from util.trigger_ws_redis_pub import trigger_ws_redis_pub
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from rest_framework_simplejwt.views import TokenObtainPairView

import json
import time
import logging, traceback
logger = logging.getLogger('users')

class DepartmentMigrationAPIView(APIView):
    def get(self, request):
        created_count = 0
        errors = []

        try:
            with transaction.atomic():
                models.Department.objects.all().delete()

                # Step 1: 조직3 (최상위)
                org3_names = old_models.User.objects.exclude(기본조직3="").values_list("기본조직3", flat=True).distinct()
                for name in org3_names:
                    name = name.strip()
                    dept, created = models.Department.objects.get_or_create(name=name, parent=None)
                    if created:
                        created_count += 1

                # Step 2: 조직2 (부모 = 조직3)
                for parent3 in models.Department.objects.filter(parent=None):
                    qs = old_models.User.objects.filter(기본조직3=parent3.name).exclude(기본조직2=parent3.name).exclude(기본조직2="")
                    org2_names = qs.values_list("기본조직2", flat=True).distinct()

                    for name in org2_names:
                        name = name.strip()
                        dept, created = models.Department.objects.get_or_create(name=name, parent=parent3)
                        if created:
                            created_count += 1

                # Step 3: 조직1 (부모 = 조직2)
                for parent3 in models.Department.objects.filter(parent=None):  # 조직3
                    qs_level2 = old_models.User.objects.filter(기본조직3=parent3.name).exclude(기본조직2="")
                    for parent2 in models.Department.objects.filter(parent=parent3):  # 조직2
                        qs_level1 = qs_level2.filter(기본조직2=parent2.name).exclude(기본조직1=parent2.name).exclude(기본조직1="")
                        org1_names = qs_level1.values_list("기본조직1", flat=True).distinct()

                        for name in org1_names:
                            name = name.strip()
                            dept, created = models.Department.objects.get_or_create(name=name, parent=parent2)
                            if created:
                                created_count += 1

            return Response({
                "message": "조직 마이그레이션 완료",
                "departments_created": created_count,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": str(e),
                "traceback": traceback.format_exc(),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UserExtensionMigrationAPIView(APIView):
    def get(self, request):
        try:
            with transaction.atomic():
                models.UserExtension.objects.all().delete()

                for old_user in old_models.User.objects.all():
                    department = self.get_department(old_user)
                    models.UserExtension.objects.create(
                        user=old_user,
                        department=department
                    )

            return Response({"message": "UserExtension 마이그레이션 완료"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": str(e),
                "traceback": traceback.format_exc(),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_department(self, old_user):
        try:
            # 조직3
            qs_3 = models.Department.objects.filter(name=old_user.기본조직3.strip() if old_user.기본조직3 else "", parent=None)
            if not qs_3.exists():
                return None
            dept_3 = qs_3.first()

            # 조직2
            qs_2 = models.Department.objects.filter(name=old_user.기본조직2.strip() if old_user.기본조직2 else "", parent=dept_3)
            if not qs_2.exists():
                return dept_3
            dept_2 = qs_2.first()

            # 조직1
            qs_1 = models.Department.objects.filter(name=old_user.기본조직1.strip() if old_user.기본조직1 else "", parent=dept_2)
            if qs_1.exists():
                return qs_1.first()
            return dept_2

        except Exception as e:
            print("get_department error:", e)
            return None

				

# class CustomTokenObtainPairView(TokenObtainPairView):
#     serializer_class = serializers.CustomTokenObtainPairSerializer

# class CompanyDBViewSet(viewsets.ModelViewSet):
# 	MODEL = CompanyDB
# 	serializer_class = serializers.CompanyDBSerializer
# 	queryset = CompanyDB.objects.all()

# 	filter_backends = [
# 		SearchFilter, 
# 		filters.DjangoFilterBackend,
# 	]
# 	search_fields = ['name']	
# 	filterset_class = customfilters.CompanyDBFilter

# 	cache_key = 'CompanyDB_list_view'
# 	cache_time = 60*60*12

# 	def get_queryset(self):
# 		queryset = cache.get(self.cache_key)
# 		if queryset is None:
# 			print ( self.cache_key, ' : no_cache', )
# 			# 캐시에 데이터가 없으면 DB에서 조회하고 캐시에 저장
# 			queryset = self.MODEL.objects.all()
# 			cache.set(self.cache_key, queryset, self.cache_time)
# 		return queryset


# class ConnectionResponse_NoAuth(APIView):
# 	"""
# 		only response to any request
# 		경우에 따라서는  (traffice등) 경우에 따라서 제거할 예정
# 	"""
# 	# authentication_classes = []
# 	permission_classes = []

# 	def get(self, request, format=None):
# 		return Response(data={'result':'ok'}, status=status.HTTP_200_OK)
	
# class ConnectionResponse_Auth(APIView):
# 	permission_classes = [IsAuthenticated]

# 	def get(self, request, format=None):
# 		return Response(data={'result':'ok'}, status=status.HTTP_200_OK)


# class UserViewSet(mixins.ListModelMixin, 
# 				  viewsets.GenericViewSet):

# 	serializer_class = serializers.UserSerializer
# 	queryset = User.objects.filter(is_active=True).order_by('기본조직3','기본조직2','기본조직1','user_성명')
# 	# authentication_classes = [SessionAuthentication, BasicAuthentication,TokenAuthentication]
# 	# permission_classes = [IsAdminUser]
# 	permission_classes = [IsAuthenticated]
# 	filter_backends = [
# 		SearchFilter, 
# 		filters.DjangoFilterBackend,
# 	]
# 	search_fields =['user_성명', 'user_mailid','기본조직1','기본조직2','기본조직3'] 

# 	cache_key = 'user_list_view'
# 	cache_time = 60*60*12

# 	def get_queryset(self):
# 		# 캐시에서 데이터 조회
# 		queryset = cache.get(self.cache_key)
# 		if queryset is None:
# 			print ( 'User_ViewSet: no_cache', )
# 			# 캐시에 데이터가 없으면 DB에서 조회하고 캐시에 저장
# 			queryset = User.objects.filter(is_active=True).order_by('기본조직3','기본조직2','기본조직1','user_성명')
# 			cache.set(self.cache_key, queryset, self.cache_time)
# 		return queryset

# class User관리_ViewSet(BaseModelViewSet):
# 	MODEL = User
# 	use_cache = False
# 	APP_ID = 179
# 	serializer_class = serializers.UserSerializer
# 	queryset = MODEL.objects.all()

# 	default_password = '123451q!'

# 	search_fields =['user_성명', 'user_mailid','기본조직1','기본조직2','기본조직3'] 
# 	filterset_class =  customfilters.User관리_Filter
# 	ordering_fields = ['기본조직3','기본조직2','기본조직1','user_성명']
# 	ordering = ['기본조직3','기본조직2','기본조직1','user_성명']

# 	handle_name = 'active_users'

# 	def get_queryset(self):
# 		return self.MODEL.objects.exclude(id=1)
	
# 	def create(self, request, *args, **kwargs):
# 		if isinstance(request.data, QueryDict):  # optional
# 			request.data._mutable = True
# 			from django.contrib.auth.hashers import make_password
# 			request.data['password'] = make_password(self.default_password)
# 		return super().create(request, *args, **kwargs )
	
# 	@action(detail=True, methods=['get'], url_path='reset-password')
# 	def reset_password(self, request, *args, **kwargs):
# 		user = self.get_object()
# 		logger.info(f"reset_password_user: {user}")
# 		user.set_password(self.default_password)
# 		user.save()
# 		return Response(status=status.HTTP_200_OK, data={'result':'success'})
	
# 	@action(detail=False, methods=['get'], url_path='request_ws_redis_publish')
# 	def request_ws_redis_publish(self, request, *args, **kwargs):
# 		try:
# 			trigger_ws_redis_pub(handle_name=self.handle_name)
# 			return Response(status=status.HTTP_200_OK, data={'result':'success'})
# 		except Exception as e:
# 			data = {'error':str(e)}
# 			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data= data)



# class Api_App권한_User_M2M_ViewSet(viewsets.ModelViewSet):
# 	MODEL = Api_App권한_User_M2M
# 	serializer_class = serializers.Api_App권한_User_M2MSerializer
# 	queryset = Api_App권한_User_M2M.objects.all()
# 	parser_classes = [MultiPartParser, FormParser, JSONParser]
# 	filter_backends = [
# 		SearchFilter, 
# 		filters.DjangoFilterBackend,
# 	]
# 	search_fields = ['user__user_성명', 'app_권한__name']
# 	# filterset_class = customfilters.Api_App권한_User_M2M_Filter


# 	def get_queryset(self):
# 		return ( Api_App권한_User_M2M.objects
# 		  		.select_related('user', 'app_권한')
# 				.order_by('user__user_성명', 'app_권한__name')
# 		)
	
# 	@action(detail=False, methods=['post'], url_path='bulk-generate')
# 	def bulk_generate(self, request, *args, **kwargs):
# 		try:
# 			### added : app_id, user_id
# 			### removed : db id이다.
# 			logger.info(f"request.data: {request.data}")
# 			app_id = request.data.get('app_id', None)
# 			added = request.data.get('added', [])
# 			removed = request.data.get('removed', [])
			
# 			# 변수 미리 초기화
# 			bulk_create_list = []
			
# 			# 문자열로 전달된 경우 JSON으로 파싱
# 			if added:
# 				added = json.loads(added) if isinstance(added, str) else added
# 				if added:
# 					# 한 번의 쿼리로 이미 존재하는 관계 확인
# 					existing_relations = set(Api_App권한_User_M2M.objects.filter(
# 						app_권한_id=app_id, 
# 						user_id__in=added
# 					).values_list('user_id', flat=True))
					
# 					# 존재하지 않는 관계만 생성
# 					bulk_create_list = [
# 						Api_App권한_User_M2M(app_권한_id=app_id, user_id=user_id)
# 						for user_id in added if user_id not in existing_relations
# 					]
			
# 			if removed:
# 				removed = json.loads(removed) if isinstance(removed, str) else removed
			
# 			logger.info(f"app_id: {app_id}, added: {added}, removed: {removed}")
			
# 			with transaction.atomic():                    
# 				if bulk_create_list:
# 					Api_App권한_User_M2M.objects.bulk_create(bulk_create_list)
# 					logger.info(f"{len(bulk_create_list)}개 항목 추가됨")
				
# 				if removed:
# 					# removed에는 Api_App권한_User_M2M 모델의 ID 값이 들어있음
# 					logger.info(f"removed: {removed}")
# 					deleted_count = Api_App권한_User_M2M.objects.filter(
# 						app_권한_id= app_id,
# 						user_id__in=removed
# 					).delete()[0]
# 					logger.info(f"{deleted_count}개 항목 삭제됨")
			
# 			# 앱 권한 데이터 가져오기
# 			prefix = Util.get_cache_prefix_for_viewset(viewset_cls=Api_App개발자_ViewSet)
# 			logger.info(f"prefix: {prefix}")
# 			if prefix:
# 				cache.delete_pattern(f"{prefix}:*")
# 				logger.info(f"캐시 삭제됨: {prefix}")

# 			app_권한 = Api_App권한.objects.get(id=int(app_id))
# 			app_data = serializers.Api_App권한Serializer(app_권한).data
# 			return Response(data=app_data, status=status.HTTP_200_OK)
			
# 		except Exception as e:
# 			logger.error(f"bulk_generate 오류: {str(e)}")
# 			logger.error(traceback.format_exc())
# 			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
# 		# finally:
# 		# 	# 성공 또는 실패와 관계없이 시그널 다시 연결
# 		# 	post_save.connect(Api_App권한_changed, sender=self.MODEL)
# 		# 	post_delete.connect(Api_App권한_changed, sender=self.MODEL)

# def add_admin_to_App_User_M2M(app_instance:Api_App권한, user_id:int = 1):
# 	""" APP instance를 받아서, user_id를 받아 사용자 추가 (기본은 관리자 )"""
# 	user = User.objects.get(id=user_id)
# 	if not Api_App권한_User_M2M.objects.filter(app_권한 = app_instance , user = user ).exists():
# 		Api_App권한_User_M2M.objects.create(app_권한 = app_instance , user = user )
# 		return True
# 	return False


# class Api_App권한_Admin_Check_Api_View(APIView):
# 	""" 전체 APP에 관리자 권한 추가 """
# 	permission_classes = [IsAuthenticated]

# 	def get(self, request, *args, **kwargs):
# 		if request.user.id != 1:
# 			return Response(status=status.HTTP_403_FORBIDDEN, data={'result':'forbidden user'})
# 		result:list[bool] = []
# 		with transaction.atomic():
# 			for app_instance in Api_App권한.objects.all():
# 				_created = add_admin_to_App_User_M2M(app_instance )
# 				result.append(_created)

# 		msg = f" 총 APP수 : {len(result)}개 =>  생성됨: {sum(result)}개, 이미 존재: {len(result) - sum(result)}개"
# 		return Response(status=status.HTTP_200_OK, data={'result':msg})


# class App권한_User_M2M_Snapshot_ViewSet(viewsets.ModelViewSet):
# 	MODEL = App권한_User_M2M_Snapshot
# 	serializer_class = serializers.App권한_User_M2M_SnapshotSerializer
# 	queryset = App권한_User_M2M_Snapshot.objects.all()
# 	ordering_fields = ['timestamp']
# 	ordering = ['-timestamp']

# 	def get_queryset(self):
# 		return App권한_User_M2M_Snapshot.objects.all().order_by(*self.ordering)
	
# 	@action(detail=True, methods=['get'], url_path='restore')
# 	def restore(self, request, *args, **kwargs):
# 		with transaction.atomic():
# 			instance = self.get_object()
			
# 			# 1. 기존 권한 삭제
# 			Api_App권한_User_M2M.objects.filter(app_권한_id__in=[
# 				item['app_권한_id'] for item in instance.data
# 			]).delete()

# 			# 2. dict → 모델 인스턴스 변환
# 			new_objs = [
# 				Api_App권한_User_M2M(app_권한_id=item['app_권한_id'], user_id=item['user_id'])
# 				for item in instance.data
# 			]
# 			Api_App권한_User_M2M.objects.bulk_create(new_objs)
# 		return Response(status=status.HTTP_200_OK, data={'result':'success'})

# class Api_App개발자_ViewSet(BaseModelViewSet):
# # class Api_App개발자_ViewSet(viewsets.ModelViewSet):
# 	use_cache = False
# 	MODEL = Api_App권한
# 	APP_ID = 153
# 	serializer_class = serializers.Api_App권한Serializer 
# 	parser_classes = [MultiPartParser, FormParser, JSONParser]
# 	queryset = Api_App권한.objects.order_by('순서','div','name')

# 	search_fields = ['div','name','표시명_구분','표시명_항목',]
# 	filterset_class = Api_App권한_FilterSet
# 	ordering_fields = ['순서','div','name']
# 	ordering = ['순서','div','name']

# 	handle_name = 'app_권한'
	
# 	def get_queryset(self):
# 		queryset = Api_App권한.objects.prefetch_related(
# 				Prefetch('app_권한_users', queryset=Api_App권한_User_M2M.objects.select_related('user'))
# 			).all()
# 		return queryset
	
# 	def add_admin_instance(self, instance):
# 		### 관리자 권한 추가
# 		if not Api_App권한_User_M2M.objects.filter(app_권한 = instance , user = self.request.user ).exists():
# 			Api_App권한_User_M2M.objects.create(app_권한 = instance , user = self.request.user )

# 	@action(detail=False, methods=['get'], url_path='snapshot-app-users')
# 	def snapshot_app_users(self, request, *args, **kwargs):
# 		### 모든 사용자의 앱 권한 스냅샷 생성
# 		s_time = time.perf_counter()
# 		with transaction.atomic():
# 			all_data = list(Api_App권한_User_M2M.objects.all().values('app_권한_id', 'user_id'))
# 			App권한_User_M2M_Snapshot.objects.create(
# 				data=all_data
# 			)
# 		e_time = time.perf_counter()
# 		logger.info(f"snapshot_app_users 소요시간: {e_time - s_time}초")
# 		return Response(status=status.HTTP_200_OK, data={'result':'success', 'time':e_time - s_time})

# 	@transaction.atomic
# 	def create(self, request, *args, **kwargs):		
# 		logger.debug(f"request.data: {request.data}")
# 		serializer = self.get_serializer(data=request.data)
# 		serializer.is_valid(raise_exception=True)
# 		instance = serializer.save()

# 		self.add_admin_instance(instance)

# 		headers = self.get_success_headers(serializer.data)
# 		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
	


# 	@transaction.atomic
# 	def update(self, request, *args, **kwargs):
# 		logger.debug(f"request.data: {request.data}")
# 		instance = self.get_object()

# 		serializer = self.get_serializer(instance, data=request.data, partial=True)
# 		serializer.is_valid(raise_exception=True)
# 		updated_instance = serializer.save()

# 		self.add_admin_instance(updated_instance)

# 		return Response(serializer.data)
	
# 	@action(detail=False, methods=['get'], url_path='request_ws_redis_publish')
# 	def request_ws_redis_publish(self, request, *args, **kwargs):
# 		try:
# 			trigger_ws_redis_pub(handle_name=self.handle_name)
# 			return Response(status=status.HTTP_200_OK, data={'result':'success'})
# 		except Exception as e:
# 			data = {'error':str(e)}
# 			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data= data)


# 	@action(detail=True, methods=['get', 'delete'], url_path='manage_table_config')
# 	def manage_table_config(self, request, *args, **kwargs):
# 		try:
# 			from util.generate_tableconfig_from_app_auth import create_table_config

# 			instance : Api_App권한 = self.get_object()
# 			table_name = f"{instance.div}_{instance.name}_appID_{instance.id}"
# 			table_instance, _created = Config_models.Table.objects.get_or_create(table_name=table_name)

# 			if request.method == 'GET':
# 				### create or update table config
# 				if not (instance.TO_MODEL and instance.TO_Serializer):
# 					return Response(status=status.HTTP_400_BAD_REQUEST, data={'result':'error', 'message':'TO_MODEL or TO_Serializer is not set'})

# 				if _created:					
# 					if not create_table_config(app_auth_instance=instance, table_instance=table_instance):
# 						return Response(status=status.HTTP_400_BAD_REQUEST, data={'result':'error', 'message':'table_config create failed'})
# 				else:
# 					from config.models import Table_Config
# 					Table_Config.objects.filter(table=table_instance).delete()
# 					if not create_table_config(app_auth_instance=instance, table_instance=table_instance):
# 						return Response(status=status.HTTP_400_BAD_REQUEST, data={'result':'error', 'message':'table_config create failed'})

# 				# Table_RedisTrigger_Mixin.trigger_ws_redis_pub(self, handle_name='table_total_config')
# 				return Response(status=status.HTTP_200_OK, data={'result':'success'})

# 			elif request.method == 'DELETE':
# 				with transaction.atomic():
# 					table_instance.delete()
# 				# Table_RedisTrigger_Mixin.trigger_ws_redis_pub(self,handle_name='table_total_config')
				
# 				return Response(status=status.HTTP_204_NO_CONTENT)

# 		except Exception as e:
# 			logger.error(f"manage_table_config 오류: {str(e)}")
# 			logger.error(traceback.format_exc())
# 			return Response(status=status.HTTP_400_BAD_REQUEST)




# 	@action(detail=False, methods=['post'], url_path='bulk_generate_with_files')
# 	def bulk_generate_with_files(self, request, *args, **kwargs):
# 		from users.signals import Api_App권한_changed  # 이 부분을 함수 내로 이동
# 		try:
# 			# 필수 데이터 확인
# 			if 'datas' not in request.data:
# 				return Response(
# 					{'error': '필수 데이터 필드 "datas"가 없습니다.'},
# 					status=status.HTTP_400_BAD_REQUEST
# 				)
			
# 			# JSON 데이터 파싱
# 			try:
# 				data_list = json.loads(request.data.get('datas'))
# 				if not isinstance(data_list, list):
# 					return Response(
# 						{'error': '"datas" 필드는 JSON 배열이어야 합니다.'},
# 						status=status.HTTP_400_BAD_REQUEST
# 					)
# 			except json.JSONDecodeError:
# 				return Response(
# 					{'error': '"datas" 필드의 JSON 형식이 올바르지 않습니다.'},
# 					status=status.HTTP_400_BAD_REQUEST
# 				)
			
# 			# 파일 데이터 처리
# 			files = request.FILES
# 			logger.info(f"bulk_generate_with_files: 데이터 {len(data_list)}개, 파일 {len(files)}개")
# 			logger.info(f"files: {files}")
			
# 			# 모델 필드 가져오기
# 			model_fields = [field.name for field in self.MODEL._meta.get_fields()]
# 			file_fields = [field.name for field in self.MODEL._meta.get_fields() 
# 						if hasattr(field, 'upload_to')]

# 			# 데이터 전처리 (트랜잭션 외부에서 수행)
# 			results = []
# 			processed_items = []

# 			### 데이터 전처리
# 			for item in data_list:
# 				logger.info(f"item: {item}")
# 				# 모델에 없는 필드 제거
# 				for key in list(item.keys()):
# 					if key not in model_fields:
# 						item.pop(key, None)
				
# 				# 파일 필드 처리
# 				item_id = item.get('id', 'new')
# 				for field_name in file_fields:
# 					file_key = f"{item_id}_{field_name}"
# 					if file_key in files:
# 						item[field_name] = files[file_key]
				
# 				processed_items.append(item)

# 			# 시그널 핸들러 임시 연결 해제
# 			# post_save.disconnect(Api_App권한_changed, sender=self.connect_signalsMODEL)
# 			# post_delete.disconnect(Api_App권한_changed, sender=self.MODEL)
# 			# 실제 DB 작업은 트랜잭션 내에서 수행
# 			instance_list_created = []
# 			with transaction.atomic():
# 				for item in processed_items:
# 					# 항목 생성 또는 업데이트
# 					if item.get('id') and int(item.get('id')) > 0:
# 						# 기존 항목 업데이트
# 						instance = self.MODEL.objects.get(id=item['id'])
# 						serializer = self.get_serializer(instance, data=item, partial=True)
# 						serializer.is_valid(raise_exception=True)
# 						instance = serializer.save()
# 						results.append({'id': instance.id, 'status': 'updated'})
# 					else:
# 						# 신규 항목 생성
# 						if 'id' in item and (not item['id'] or int(item['id']) <= 0):
# 							item.pop('id')
# 						serializer = self.get_serializer(data=item)
# 						serializer.is_valid(raise_exception=True)
# 						instance = serializer.save()
# 						results.append({'id': instance.id, 'status': 'created'})
# 						instance_list_created.append(instance)
# 						if not Api_App권한_User_M2M.objects.filter(app_권한 = instance , user = self.request.user ).exists():
# 							Api_App권한_User_M2M.objects.create(app_권한 = instance , user = self.request.user )


# 			return Response({
# 				'result': True, 
# 				'message': f'{len(data_list)}개 항목 처리 완료',
# 				'processed_items': results
# 			}, status=status.HTTP_200_OK)
				
# 		except Exception as e:
# 			logger.error(f"bulk_generate_with_files 처리 중 오류 발생: {str(e)}")
# 			logger.error(traceback.format_exc())
# 			return Response({
# 				'result': False, 
# 				'error': str(e)
# 			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 	def send_bulk_update_signal(self, data_list):
# 		"""
# 		bull 처리 완료 후 한 번만 시그널을 발생시키는 메소드
# 		"""
# 		try:
# 			# Redis pub 또는 필요한 시그널 로직 구현
# 			# 예: signals.api_app_권한_updated.send(sender=self.MODEL, instance=None, bulk_data=data_list)
# 			from django.db.models.signals import post_save
# 			from django.dispatch import receiver
			
# 			# 임시 인스턴스 생성 또는 대표 인스턴스 사용
# 			if data_list and len(data_list) > 0:
# 				if isinstance(data_list[0], dict) and 'id' in data_list[0] and data_list[0]['id']:
# 					instance = self.MODEL.objects.get(id=data_list[0]['id'])
# 					# post_save 시그널 수동 발생
# 					post_save.send(sender=self.MODEL, instance=instance, created=False, update_fields=None, raw=False, using='default')
# 					logger.info(f"Bulk 업데이트 후 시그널 발생 완료: {instance}")
# 		except Exception as e:
# 			logger.error(f"시그널 발생 중 오류: {str(e)}")



# class Api_App권한ViewSet(Api_App개발자_ViewSet):

# 	def get_queryset(self):
# 		queryset = super().get_queryset().exclude(name__contains='개발자')
# 		return queryset

	



	
# class Api_App권한_사용자별_Api_View ( APIView):
# 	permission_classes = [IsAuthenticated]

# 	def get_send_data(self, user_id: int) -> list:
# 		# 1. 전체 App 권한 목록
# 		qs_app권한 = Api_App권한.objects.filter(
# 			is_Active=True, is_dev=False
# 		).order_by('순서', 'div', 'name')

# 		# 2. 해당 사용자의 권한 관계
# 		qs_권한 = Api_App권한_User_M2M.objects.filter(user_id=user_id)
# 		map_app권한_id_to_obj = {
# 			obj.app_권한_id: obj for obj in qs_권한
# 		}

# 		# 3. 응답 데이터 구성
# 		send_data = []
# 		for app권한 in qs_app권한:
# 			serializer = serializers.Api_App권한Serializer_for_개인별(app권한)
# 			data = serializer.data

# 			# serializer의 id를 'app_권한_id'로 리네이밍
# 			data['app_권한_id'] = data.pop('id', None)

# 			# 해당 사용자 권한 연결 여부 및 연결 ID
# 			m2m_obj = map_app권한_id_to_obj.get(app권한.id)
# 			data['id'] = m2m_obj.id if m2m_obj else -1
# 			data['is_user'] = m2m_obj is not None
# 			data['user_id'] = user_id

# 			send_data.append(data)

# 		return send_data

# 	def get_user_id_from_request(self, request):
# 		user_id = request.query_params.get('user_id')
# 		if not user_id:
# 			return Response({"detail": "user_id는 필수입니다."}, status=400)
# 		try:
# 			user_id = int(user_id)
# 		except ValueError:
# 			return Response({"detail": "user_id는 숫자여야 합니다."}, status=400)
# 		return user_id
	

# 	def get(self, request, *args, **kwargs):
# 		# 1. GET 파라미터로 user_id 받기
# 		result = self.get_user_id_from_request(request)
# 		if isinstance(result, Response):
# 			return result
# 		else:
# 			user_id = result

# 		send_data = self.get_send_data(user_id)
# 		return Response(send_data)
	
# 	def post(self, request, *args, **kwargs):
# 		# 1. GET 파라미터로 user_id 받기
# 		try:
# 			result = self.get_user_id_from_request(request)
# 			if isinstance(result, Response):
# 				return result
# 			else:
# 				user_id = result

# 			data_list = request.data  # list of dicts
# 			to_create = []
# 			to_delete_ids = []

# 			for item in data_list:
# 				app권한_id = item.get('app_권한_id')
# 				m2m_id = item.get('id')
# 				is_user = item.get('is_user')

# 				if m2m_id == -1 and is_user:  # 새로 추가할 항목
# 					to_create.append(Api_App권한_User_M2M(user_id=user_id, app_권한_id=app권한_id))
# 				elif m2m_id > 0 and not is_user:  # 삭제할 항목
# 					to_delete_ids.append(m2m_id)

# 			with transaction.atomic():
# 				if to_create:
# 					Api_App권한_User_M2M.objects.bulk_create(to_create)
# 				if to_delete_ids:
# 					Api_App권한_User_M2M.objects.filter(id__in=to_delete_ids).delete()
# 			return Response(self.get_send_data(user_id))
# 		except Exception as e:
# 			logger.error(f"post 오류: {str(e)}")
# 			return Response({"detail": f"오류가 발생했습니다.{str(e)}"}, status=500)



# class User_Info(APIView):
# 	""" DB FILED VIEW {NAME:TYPE}"""
# 	MODEL = User

# 	# authentication_classes = []
# 	permission_classes = [IsAuthenticated]

# 	def get(self, request, format=None):
# 		return Response ( serializers.UserSerializer(request.user).data )


# class PasswordChangeView(APIView):
# 	permission_classes = [IsAuthenticated]
	
# 	def post(self, request):
# 		serializer = serializers.PasswordChangeSerializer(data=request.data)
# 		if serializer.is_valid():
# 			user = request.user
# 			if user.check_password(serializer.validated_data['old_password']):
#                # 현재 사용 중인 토큰만 블랙리스트에 추가
#                 # 모든 토큰을 블랙리스트에 추가하는 대신 현재 토큰만 처리

# 				# 사용자의 모든 리프레시 토큰을 블랙리스트에 추가
# 				try:
# 					outstanding_tokens = OutstandingToken.objects.filter(user=user)
# 					for token in outstanding_tokens:
# 						BlacklistedToken.objects.get_or_create(token=token)
# 					logger.info(f"사용자 {user.user_성명}의 모든 토큰이 블랙리스트에 추가되었습니다.")
# 				except Exception as e:
# 					logger.error(f"토큰 블랙리스트 처리 중 오류: {str(e)}")

# 				user.set_password(serializer.validated_data['new_password'])
# 				user.save()
				
# 				# 새 토큰 생성
# 				refresh = RefreshToken.for_user(user)
				
# 				return Response({
# 					'message': '비밀번호가 성공적으로 변경되었습니다.',
# 					'tokens': {
# 						'refresh': str(refresh),
# 						'access': str(refresh.access_token),
# 					}
# 				}, status=status.HTTP_200_OK)
# 			return Response({'error': '현재 비밀번호가 올바르지 않습니다.'}, 
# 							status=status.HTTP_400_BAD_REQUEST)
# 		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# from django.contrib.auth import get_user_model
# from rest_framework.decorators import api_view, permission_classes
# User = get_user_model()

# @api_view(['POST'])
# @permission_classes([IsAdminUser])  # 관리자만 접근 가능
# def reset_user_password(request):
# 	user_id = request.data.get('user_id')
# 	default_password = '123451q!'  # 초기 비밀번호 설정
	
# 	try:
# 		user = User.objects.get(id=user_id)
# 		user.set_password(default_password)
# 		user.save()
		
# 		return Response({
# 			'message': '비밀번호가 성공적으로 초기화되었습니다.',
# 			'default_password': default_password
# 		}, status=status.HTTP_200_OK)
		
# 	except User.DoesNotExist:
# 		return Response({
# 			'error': '사용자를 찾을 수 없습니다.'
# 		}, status=status.HTTP_404_NOT_FOUND)




# class ErrorLog_ViewSet(viewsets.ModelViewSet):
# 	MODEL = ErrorLog
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.ErrorLogSerializer
# 	parser_classes = [MultiPartParser, FormParser]

# 	filter_backends = [
# 		   SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]

# 	# filterset_class = Api_App사용자_FilterSet

# 	def get_queryset(self):
# 		return self.MODEL.objects.order_by('-id')

