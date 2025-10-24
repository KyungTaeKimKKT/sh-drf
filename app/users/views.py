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
from django.utils import timezone

from util.base_model_viewset import BaseModelViewSet

from .models import User, Api_App권한, Api_App권한_User_M2M, CompanyDB, ErrorLog, App권한_User_M2M_Snapshot, Portal_Info, Portal_Permission
import config.models as Config_models
from util.customfilters import *
# from .permissons import CustomPermission
from . import serializers, customfilters
import util.utils_func as Util
from util.trigger_ws_redis_pub import trigger_ws_redis_pub
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.contrib.auth import authenticate

import util.cache_manager as CacheManager
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
import json
import time
import logging, traceback
logger = logging.getLogger('users')

class Facelogin_RefreshTokenView(APIView):
	permission_classes = [IsAuthenticated]
	
	def post(self, request):
		try:
			refresh_token = request.data.get('refresh', None)
			if not refresh_token:
				return Response({"detail": "Missing token"}, status=401)

			# 기존 토큰 검증
			old_refresh = RefreshToken(refresh_token)
			user_id = old_refresh.payload.get('user_id')
			user = User.objects.get(id=user_id)
			self.user = user
			print ("user:", user)

			# DRF 세팅 기준으로 새 토큰 발급
			new_refresh = RefreshToken.for_user(user)
			data = {
				'refresh': str(new_refresh),
				'access': str(new_refresh.access_token),
				'user_info': serializers.UserSerializer(self.user).data,
				'ws_url_db': CacheManager.get_ws_url_db_all(),
				'is_app_admin': self.get_is_app_admin(),
				'is_table_config_admin': self.get_is_table_config_admin()
			}
			return Response(data)

		except Exception as e:
			return Response({"detail": f"Invalid token : {e}"}, status=401)

	def get_is_app_admin(self):
		qs = Api_App권한_User_M2M.objects.filter(user = self.user, app_권한__div__icontains='app설정',  app_권한__name__icontains='app설정')
		return qs.exists()

	def get_is_table_config_admin(self):
		qs = Api_App권한_User_M2M.objects.filter(user = self.user, app_권한__div__icontains='config',  app_권한__name__icontains='table')
		return qs.exists()



class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CompanyDBViewSet(viewsets.ModelViewSet):
	MODEL = CompanyDB
	serializer_class = serializers.CompanyDBSerializer
	queryset = CompanyDB.objects.all()

	filter_backends = [
		SearchFilter, 
		filters.DjangoFilterBackend,
	]
	search_fields = ['name']	
	filterset_class = customfilters.CompanyDBFilter

	cache_key = 'CompanyDB_list_view'
	cache_time = 60*60*12

	def get_queryset(self):
		queryset = cache.get(self.cache_key)
		if queryset is None:
			print ( self.cache_key, ' : no_cache', )
			# 캐시에 데이터가 없으면 DB에서 조회하고 캐시에 저장
			queryset = self.MODEL.objects.all()
			cache.set(self.cache_key, queryset, self.cache_time)
		return queryset


class ConnectionResponse_NoAuth(APIView):
	"""
		only response to any request
		경우에 따라서는  (traffice등) 경우에 따라서 제거할 예정
	"""
	# authentication_classes = []
	permission_classes = []

	def get(self, request, format=None):
		return Response(data={'result':'ok'}, status=status.HTTP_200_OK)
	
class ConnectionResponse_Auth(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request, format=None):
		return Response(data={'result':'ok'}, status=status.HTTP_200_OK)


class UserViewSet(mixins.ListModelMixin, 
				  viewsets.GenericViewSet):

	serializer_class = serializers.UserSerializer
	queryset = User.objects.filter(is_active=True).order_by('기본조직3','기본조직2','기본조직1','user_성명')
	# authentication_classes = [SessionAuthentication, BasicAuthentication,TokenAuthentication]
	# permission_classes = [IsAdminUser]
	permission_classes = [IsAuthenticated]
	filter_backends = [
		SearchFilter, 
		filters.DjangoFilterBackend,
	]
	search_fields =['user_성명', 'user_mailid','기본조직1','기본조직2','기본조직3'] 

	cache_key = 'user_list_view'
	cache_time = 60*60*12

	def get_queryset(self):
		# 캐시에서 데이터 조회
		queryset = cache.get(self.cache_key)
		if queryset is None:
			print ( 'User_ViewSet: no_cache', )
			# 캐시에 데이터가 없으면 DB에서 조회하고 캐시에 저장
			queryset = User.objects.filter(is_active=True).order_by('기본조직3','기본조직2','기본조직1','user_성명')
			cache.set(self.cache_key, queryset, self.cache_time)
		return queryset

class User관리_ViewSet(BaseModelViewSet):
	MODEL = User
	use_cache = False
	APP_ID = 179
	serializer_class = serializers.UserSerializer
	queryset = MODEL.objects.all()

	default_password = '123451q!'

	search_fields =['user_성명', 'user_mailid','기본조직1','기본조직2','기본조직3'] 
	filterset_class =  customfilters.User관리_Filter
	ordering_fields = ['기본조직3','기본조직2','기본조직1','user_성명']
	ordering = ['기본조직3','기본조직2','기본조직1','user_성명']

	handle_name = 'active_users'

	def get_queryset(self):
		return self.MODEL.objects.exclude(id=1)
	

	@action(detail=True, methods=['get'], url_path='reset-password')
	def reset_password(self, request, *args, **kwargs):
		user = self.get_object()
		# logger.info(f"reset_password_user: {user}")
		user.set_password(self.default_password)
		user.save()
		serializer = self.get_serializer(user)
		return Response(status=status.HTTP_200_OK, data=serializer.data)
	
	@action(detail=False, methods=['get'], url_path='request_ws_redis_publish')
	def request_ws_redis_publish(self, request, *args, **kwargs):
		try:
			trigger_ws_redis_pub(handle_name=self.handle_name)
			return Response(status=status.HTTP_200_OK, data={'result':'success'})
		except Exception as e:
			data = {'error':str(e)}
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data= data)


	@action(detail=False, methods=['get'], url_path='template')
	def template(self, request, *args, **kwargs):
		### 템플릿 생성
		instance = self.MODEL.objects.get(id=1)
		serializer = self.get_serializer(instance)
		#### 약간의 추가적 처리
		data = serializer.data.copy()
		data['id'] = -instance.id
		for key, value in data.items():
			if isinstance(value, bool):
				data[key] = False
			elif isinstance(value, str):
				data[key] = ''

		return Response(status=status.HTTP_200_OK, data=data)



class Api_App권한_User_M2M_ViewSet(viewsets.ModelViewSet):
	MODEL = Api_App권한_User_M2M
	serializer_class = serializers.Api_App권한_User_M2MSerializer
	queryset = Api_App권한_User_M2M.objects.all()
	parser_classes = [MultiPartParser, FormParser, JSONParser]
	filter_backends = [
		SearchFilter, 
		filters.DjangoFilterBackend,
	]
	search_fields = ['user__user_성명', 'app_권한__name']
	# filterset_class = customfilters.Api_App권한_User_M2M_Filter


	def get_queryset(self):
		return ( Api_App권한_User_M2M.objects
		  		.select_related('user', 'app_권한')
				.order_by('user__user_성명', 'app_권한__name')
		)
	
	@action(detail=False, methods=['post'], url_path='bulk-generate')
	def bulk_generate(self, request, *args, **kwargs):
		try:
			### added : app_id, user_id
			### removed : db id이다.
			logger.info(f"request.data: {request.data}")
			app_id = request.data.get('app_id', None)
			added = request.data.get('added', [])
			removed = request.data.get('removed', [])
			
			# 변수 미리 초기화
			bulk_create_list = []
			
			# 문자열로 전달된 경우 JSON으로 파싱
			if added:
				added = json.loads(added) if isinstance(added, str) else added
				if added:
					# 한 번의 쿼리로 이미 존재하는 관계 확인
					existing_relations = set(Api_App권한_User_M2M.objects.filter(
						app_권한_id=app_id, 
						user_id__in=added
					).values_list('user_id', flat=True))
					
					# 존재하지 않는 관계만 생성
					bulk_create_list = [
						Api_App권한_User_M2M(app_권한_id=app_id, user_id=user_id)
						for user_id in added if user_id not in existing_relations
					]
			
			if removed:
				removed = json.loads(removed) if isinstance(removed, str) else removed
			
			logger.info(f"app_id: {app_id}, added: {added}, removed: {removed}")
			
			with transaction.atomic():                    
				if bulk_create_list:
					Api_App권한_User_M2M.objects.bulk_create(bulk_create_list)
					logger.info(f"{len(bulk_create_list)}개 항목 추가됨")
				
				if removed:
					# removed에는 Api_App권한_User_M2M 모델의 ID 값이 들어있음
					logger.info(f"removed: {removed}")
					deleted_count = Api_App권한_User_M2M.objects.filter(
						app_권한_id= app_id,
						user_id__in=removed
					).delete()[0]
					logger.info(f"{deleted_count}개 항목 삭제됨")
			
			# 앱 권한 데이터 가져오기
			prefix = Util.get_cache_prefix_for_viewset(viewset_cls=Api_App개발자_ViewSet)
			logger.info(f"prefix: {prefix}")
			if prefix:
				cache.delete_pattern(f"{prefix}:*")
				logger.info(f"캐시 삭제됨: {prefix}")

			app_권한 = Api_App권한.objects.get(id=int(app_id))
			app_data = serializers.Api_App권한Serializer(app_권한).data
			return Response(data=app_data, status=status.HTTP_200_OK)
			
		except Exception as e:
			logger.error(f"bulk_generate 오류: {str(e)}")
			logger.error(traceback.format_exc())
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
		# finally:
		# 	# 성공 또는 실패와 관계없이 시그널 다시 연결
		# 	post_save.connect(Api_App권한_changed, sender=self.MODEL)
		# 	post_delete.connect(Api_App권한_changed, sender=self.MODEL)

def add_admin_to_App_User_M2M(app_instance:Api_App권한, user_id:int = 1):
	""" APP instance를 받아서, user_id를 받아 사용자 추가 (기본은 관리자 )"""
	user = User.objects.get(id=user_id)
	if not Api_App권한_User_M2M.objects.filter(app_권한 = app_instance , user = user ).exists():
		Api_App권한_User_M2M.objects.create(app_권한 = app_instance , user = user )
		return True
	return False


class Api_App권한_Admin_Check_Api_View(APIView):
	""" 전체 APP에 관리자 권한 추가 """
	permission_classes = [IsAuthenticated]

	def get(self, request, *args, **kwargs):
		if request.user.id != 1:
			return Response(status=status.HTTP_403_FORBIDDEN, data={'result':'forbidden user'})
		result:list[bool] = []
		with transaction.atomic():
			for app_instance in Api_App권한.objects.all():
				_created = add_admin_to_App_User_M2M(app_instance )
				result.append(_created)

		msg = f" 총 APP수 : {len(result)}개 =>  생성됨: {sum(result)}개, 이미 존재: {len(result) - sum(result)}개"
		return Response(status=status.HTTP_200_OK, data={'result':msg})


class App권한_User_M2M_Snapshot_ViewSet(viewsets.ModelViewSet):
	MODEL = App권한_User_M2M_Snapshot
	serializer_class = serializers.App권한_User_M2M_SnapshotSerializer
	queryset = App권한_User_M2M_Snapshot.objects.all()
	ordering_fields = ['timestamp']
	ordering = ['-timestamp']

	def get_queryset(self):
		return App권한_User_M2M_Snapshot.objects.all().order_by(*self.ordering)
	
	@action(detail=True, methods=['get'], url_path='restore')
	def restore(self, request, *args, **kwargs):
		with transaction.atomic():
			instance = self.get_object()
			
			# 1. 기존 권한 삭제
			Api_App권한_User_M2M.objects.filter(app_권한_id__in=[
				item['app_권한_id'] for item in instance.data
			]).delete()

			# 2. dict → 모델 인스턴스 변환
			new_objs = [
				Api_App권한_User_M2M(app_권한_id=item['app_권한_id'], user_id=item['user_id'])
				for item in instance.data
			]
			Api_App권한_User_M2M.objects.bulk_create(new_objs)
		return Response(status=status.HTTP_200_OK, data={'result':'success'})


class Api_App개발자_ViewSet(BaseModelViewSet):
# class Api_App개발자_ViewSet(viewsets.ModelViewSet):
	USE_CACHE = True
	USE_CACHE_PERMISSION = True
	MODEL = Api_App권한
	APP_ID = 153
	APP_INSTANCE = Api_App권한.objects.get(id=APP_ID)
	serializer_class = serializers.Api_App권한Serializer 
	parser_classes = [MultiPartParser, FormParser, JSONParser]
	queryset = Api_App권한.objects.order_by('순서','div','name')

	search_fields = ['div','name','표시명_구분','표시명_항목',]
	filterset_class = Api_App권한_FilterSet
	ordering_fields = ['순서','div','name']
	ordering = ['순서','div','name']

	handle_name = 'app_권한'
	cache_base = 'app_권한_개발자'
	cache_timeout = 60 * 60

	### serializer override 시 아래 내부 함수 오버라이드 필요
	def _perform_create(self, serializer):
		with transaction.atomic():
			instance = serializer.save(등록일= timezone.now() )
			self.add_admin_instance(instance)
			return instance
		
	def _perform_update(self, serializer):
		with transaction.atomic():
			instance = serializer.save()
			self.add_admin_instance(instance)
			return instance

	def _perform_destroy(self, instance):
		instance.delete()
	####
	
	def get_queryset(self):
		queryset = Api_App권한.objects.prefetch_related(
				Prefetch('app_권한_users', queryset=Api_App권한_User_M2M.objects.select_related('user'))
			).all()
		return queryset
	
	# @transaction.atomic
	# def create(self, request, *args, **kwargs):		
	# 	logger.debug(f"request.data: {request.data}")
	# 	serializer = self.get_serializer(data=request.data)
	# 	serializer.is_valid(raise_exception=True)
	# 	instance = serializer.save()

	# 	self.add_admin_instance(instance)

	# 	headers = self.get_success_headers(serializer.data)
	# 	return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
	
	# @transaction.atomic
	# def update(self, request, *args, **kwargs):
	# 	try:
	# 		print(f"request.data: {request.data}")

	# 		instance = self.get_object()

	# 		serializer = self.get_serializer(instance, data=request.data, partial=True)
	# 		serializer.is_valid(raise_exception=True)
	# 		updated_instance = serializer.save()

	# 		self.add_admin_instance(updated_instance)

	# 		return Response(serializer.data)
	# 	except Exception as e:
	# 		logger.error(f"update 오류: {str(e)}")
	# 		logger.error(f"request.data: {request.data}")
	# 		logger.error(traceback.format_exc())
	# 		return Response(status=status.HTTP_400_BAD_REQUEST, data={ 'message':str(e)})
		
		#####	
	def add_admin_instance(self, instance):
		### 관리자 권한 추가 : 조회해서 없으면 추가함.
		if not Api_App권한_User_M2M.objects.filter(app_권한 = instance , user = self.request.user ).exists():
			Api_App권한_User_M2M.objects.create(app_권한 = instance , user = self.request.user )

	@action(detail=False, methods=['get'], url_path='snapshot-app-users')
	def snapshot_app_users(self, request, *args, **kwargs):
		### 모든 사용자의 앱 권한 스냅샷 생성
		s_time = time.perf_counter()
		with transaction.atomic():
			all_data = list(Api_App권한_User_M2M.objects.all().values('app_권한_id', 'user_id'))
			App권한_User_M2M_Snapshot.objects.create(
				data=all_data
			)
		e_time = time.perf_counter()
		logger.info(f"snapshot_app_users 소요시간: {e_time - s_time}초")
		return Response(status=status.HTTP_200_OK, data={'result':'success', 'time':e_time - s_time})
	
	@action(detail=True, methods=['get'], url_path='template_copyed')
	def template_copyed(self, request, *args, **kwargs):
		instance = self.get_object()
		serializer = self.get_serializer(instance)
		data = serializer.data.copy()   # 복사 후 수정
		data['id'] = -instance.id       # id 음수 처리
		#### 약간의 추가적 처리
		_list = ['name', 'api_url','표시명_항목',]
		for _item in _list:
			data[_item] = data[_item] + '_copy'
		data['is_Active'] = False
		data['is_Run'] = False
		data['is_dev'] = True
		data['help_page'] = None
		return Response(status=status.HTTP_200_OK, data=data)


	
	@action(detail=False, methods=['get'], url_path='request_ws_redis_publish')
	def request_ws_redis_publish(self, request, *args, **kwargs):
		try:
			trigger_ws_redis_pub(handle_name=self.handle_name)
			return Response(status=status.HTTP_200_OK, data={'result':'success'})
		except Exception as e:
			data = {'error':str(e)}
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data= data)


	@action(detail=True, methods=['get', 'delete'], url_path='manage_table_config')
	def manage_table_config(self, request, *args, **kwargs):
		try:
			from util.generate_tableconfig_from_app_auth import create_table_config

			instance : Api_App권한 = self.get_object()
			table_name = f"{instance.div}_{instance.name}_appID_{instance.id}"
			table_instance, _created = Config_models.Table.objects.get_or_create(table_name=table_name)

			if request.method == 'GET':
				### create or update table config
				if not (instance.TO_MODEL and instance.TO_Serializer):
					return Response(status=status.HTTP_400_BAD_REQUEST, data={'result':'error', 'message':'TO_MODEL or TO_Serializer is not set'})

				if _created:					
					if not create_table_config(app_auth_instance=instance, table_instance=table_instance):
						return Response(status=status.HTTP_400_BAD_REQUEST, data={'result':'error', 'message':'table_config create failed'})
				else:
					from config.models import Table_Config
					Table_Config.objects.filter(table=table_instance).delete()
					if not create_table_config(app_auth_instance=instance, table_instance=table_instance):
						return Response(status=status.HTTP_400_BAD_REQUEST, data={'result':'error', 'message':'table_config create failed'})

				# Table_RedisTrigger_Mixin.trigger_ws_redis_pub(self, handle_name='table_total_config')
				return Response(status=status.HTTP_200_OK, data={'result':'success'})

			elif request.method == 'DELETE':
				with transaction.atomic():
					table_instance.delete()
				# Table_RedisTrigger_Mixin.trigger_ws_redis_pub(self,handle_name='table_total_config')
				
				return Response(status=status.HTTP_204_NO_CONTENT)

		except Exception as e:
			logger.error(f"manage_table_config 오류: {str(e)}")
			logger.error(traceback.format_exc())
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'error':str(e)})




	@action(detail=False, methods=['post'], url_path='bulk_generate_with_files')
	def bulk_generate_with_files(self, request, *args, **kwargs):
		from users.signals import Api_App권한_changed  # 이 부분을 함수 내로 이동
		try:
			# 필수 데이터 확인
			if 'datas' not in request.data:
				return Response(
					{'error': '필수 데이터 필드 "datas"가 없습니다.'},
					status=status.HTTP_400_BAD_REQUEST
				)
			
			# JSON 데이터 파싱
			try:
				data_list = json.loads(request.data.get('datas'))
				if not isinstance(data_list, list):
					return Response(
						{'error': '"datas" 필드는 JSON 배열이어야 합니다.'},
						status=status.HTTP_400_BAD_REQUEST
					)
			except json.JSONDecodeError:
				return Response(
					{'error': '"datas" 필드의 JSON 형식이 올바르지 않습니다.'},
					status=status.HTTP_400_BAD_REQUEST
				)
			
			# 파일 데이터 처리
			files = request.FILES
			logger.info(f"bulk_generate_with_files: 데이터 {len(data_list)}개, 파일 {len(files)}개")
			logger.info(f"files: {files}")
			
			# 모델 필드 가져오기
			model_fields = [field.name for field in self.MODEL._meta.get_fields()]
			file_fields = [field.name for field in self.MODEL._meta.get_fields() 
						if hasattr(field, 'upload_to')]

			# 데이터 전처리 (트랜잭션 외부에서 수행)
			results = []
			processed_items = []

			### 데이터 전처리
			for item in data_list:
				logger.info(f"item: {item}")
				# 모델에 없는 필드 제거
				for key in list(item.keys()):
					if key not in model_fields:
						item.pop(key, None)
				
				# 파일 필드 처리
				item_id = item.get('id', 'new')
				for field_name in file_fields:
					file_key = f"{item_id}_{field_name}"
					if file_key in files:
						item[field_name] = files[file_key]
				
				processed_items.append(item)

			# 시그널 핸들러 임시 연결 해제
			# post_save.disconnect(Api_App권한_changed, sender=self.connect_signalsMODEL)
			# post_delete.disconnect(Api_App권한_changed, sender=self.MODEL)
			# 실제 DB 작업은 트랜잭션 내에서 수행
			instance_list_created = []
			with transaction.atomic():
				for item in processed_items:
					# 항목 생성 또는 업데이트
					if item.get('id') and int(item.get('id')) > 0:
						# 기존 항목 업데이트
						instance = self.MODEL.objects.get(id=item['id'])
						serializer = self.get_serializer(instance, data=item, partial=True)
						serializer.is_valid(raise_exception=True)
						instance = serializer.save()
						results.append({'id': instance.id, 'status': 'updated'})
					else:
						# 신규 항목 생성
						if 'id' in item and (not item['id'] or int(item['id']) <= 0):
							item.pop('id')
						serializer = self.get_serializer(data=item)
						serializer.is_valid(raise_exception=True)
						instance = serializer.save()
						results.append({'id': instance.id, 'status': 'created'})
						instance_list_created.append(instance)
						if not Api_App권한_User_M2M.objects.filter(app_권한 = instance , user = self.request.user ).exists():
							Api_App권한_User_M2M.objects.create(app_권한 = instance , user = self.request.user )


			return Response({
				'result': True, 
				'message': f'{len(data_list)}개 항목 처리 완료',
				'processed_items': results
			}, status=status.HTTP_200_OK)
				
		except Exception as e:
			logger.error(f"bulk_generate_with_files 처리 중 오류 발생: {str(e)}")
			logger.error(traceback.format_exc())
			return Response({
				'result': False, 
				'error': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	def send_bulk_update_signal(self, data_list):
		"""
		bull 처리 완료 후 한 번만 시그널을 발생시키는 메소드
		"""
		try:
			# Redis pub 또는 필요한 시그널 로직 구현
			# 예: signals.api_app_권한_updated.send(sender=self.MODEL, instance=None, bulk_data=data_list)
			from django.db.models.signals import post_save
			from django.dispatch import receiver
			
			# 임시 인스턴스 생성 또는 대표 인스턴스 사용
			if data_list and len(data_list) > 0:
				if isinstance(data_list[0], dict) and 'id' in data_list[0] and data_list[0]['id']:
					instance = self.MODEL.objects.get(id=data_list[0]['id'])
					# post_save 시그널 수동 발생
					post_save.send(sender=self.MODEL, instance=instance, created=False, update_fields=None, raw=False, using='default')
					logger.info(f"Bulk 업데이트 후 시그널 발생 완료: {instance}")
		except Exception as e:
			logger.error(f"시그널 발생 중 오류: {str(e)}")



class Api_App권한ViewSet(Api_App개발자_ViewSet):
	cache_base = 'app_권한_관리자'
	cache_timeout = 60 * 60
	



	
class Api_App권한_사용자별_Api_View ( APIView):
	permission_classes = [IsAuthenticated]

	def get_send_data(self, user_id: int) -> list:
		# 1. 전체 App 권한 목록
		qs_app권한 = Api_App권한.objects.filter(
			is_Active=True, is_dev=False
		).order_by('순서', 'div', 'name')

		# 2. 해당 사용자의 권한 관계
		qs_권한 = Api_App권한_User_M2M.objects.filter(user_id=user_id)
		map_app권한_id_to_obj = {
			obj.app_권한_id: obj for obj in qs_권한
		}

		# 3. 응답 데이터 구성
		send_data = []
		for app권한 in qs_app권한:
			serializer = serializers.Api_App권한Serializer_for_개인별(app권한)
			data = serializer.data

			# serializer의 id를 'app_권한_id'로 리네이밍
			data['app_권한_id'] = data.pop('id', None)

			# 해당 사용자 권한 연결 여부 및 연결 ID
			m2m_obj = map_app권한_id_to_obj.get(app권한.id)
			data['id'] = m2m_obj.id if m2m_obj else -1
			data['is_user'] = m2m_obj is not None
			data['user_id'] = user_id

			send_data.append(data)

		return send_data

	def get_user_id_from_request(self, request):
		user_id = request.query_params.get('user_id')
		if not user_id:
			return Response({"detail": "user_id는 필수입니다."}, status=400)
		try:
			user_id = int(user_id)
		except ValueError:
			return Response({"detail": "user_id는 숫자여야 합니다."}, status=400)
		return user_id
	

	def get(self, request, *args, **kwargs):
		# 1. GET 파라미터로 user_id 받기
		result = self.get_user_id_from_request(request)
		if isinstance(result, Response):
			return result
		else:
			user_id = result

		send_data = self.get_send_data(user_id)
		return Response(send_data)
	
	def post(self, request, *args, **kwargs):
		# 1. GET 파라미터로 user_id 받기
		try:
			result = self.get_user_id_from_request(request)
			if isinstance(result, Response):
				return result
			else:
				user_id = result

			data_list = request.data  # list of dicts
			to_create = []
			to_delete_ids = []

			for item in data_list:
				app권한_id = item.get('app_권한_id')
				m2m_id = item.get('id')
				is_user = item.get('is_user')

				if m2m_id == -1 and is_user:  # 새로 추가할 항목
					to_create.append(Api_App권한_User_M2M(user_id=user_id, app_권한_id=app권한_id))
				elif m2m_id > 0 and not is_user:  # 삭제할 항목
					to_delete_ids.append(m2m_id)

			with transaction.atomic():
				if to_create:
					Api_App권한_User_M2M.objects.bulk_create(to_create)
				if to_delete_ids:
					Api_App권한_User_M2M.objects.filter(id__in=to_delete_ids).delete()
			return Response(self.get_send_data(user_id))
		except Exception as e:
			logger.error(f"post 오류: {str(e)}")
			return Response({"detail": f"오류가 발생했습니다.{str(e)}"}, status=500)



class User_Info(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""
	MODEL = User

	# authentication_classes = []
	permission_classes = [IsAuthenticated]

	def get(self, request, format=None):
		return Response ( serializers.UserSerializer(request.user).data )


class PasswordChangeView(APIView):
	permission_classes = [IsAuthenticated]
	
	def post(self, request):
		serializer = serializers.PasswordChangeSerializer(data=request.data)
		if serializer.is_valid():
			user = request.user
			if user.check_password(serializer.validated_data['old_password']):
               # 현재 사용 중인 토큰만 블랙리스트에 추가
                # 모든 토큰을 블랙리스트에 추가하는 대신 현재 토큰만 처리

				# 사용자의 모든 리프레시 토큰을 블랙리스트에 추가
				try:
					outstanding_tokens = OutstandingToken.objects.filter(user=user)
					for token in outstanding_tokens:
						BlacklistedToken.objects.get_or_create(token=token)
					logger.info(f"사용자 {user.user_성명}의 모든 토큰이 블랙리스트에 추가되었습니다.")
				except Exception as e:
					logger.error(f"토큰 블랙리스트 처리 중 오류: {str(e)}")

				user.set_password(serializer.validated_data['new_password'])
				user.save()
				
				# 새 토큰 생성
				refresh = RefreshToken.for_user(user)
				
				return Response({
					'message': '비밀번호가 성공적으로 변경되었습니다.',
					'tokens': {
						'refresh': str(refresh),
						'access': str(refresh.access_token),
					}
				}, status=status.HTTP_200_OK)
			return Response({'error': '현재 비밀번호가 올바르지 않습니다.'}, 
							status=status.HTTP_400_BAD_REQUEST)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
User = get_user_model()

@api_view(['POST'])
@permission_classes([IsAdminUser])  # 관리자만 접근 가능
def reset_user_password(request):
	user_id = request.data.get('user_id')
	default_password = '123451q!'  # 초기 비밀번호 설정
	
	try:
		user = User.objects.get(id=user_id)
		user.set_password(default_password)
		user.save()
		
		return Response({
			'message': '비밀번호가 성공적으로 초기화되었습니다.',
			'default_password': default_password
		}, status=status.HTTP_200_OK)
		
	except User.DoesNotExist:
		return Response({
			'error': '사용자를 찾을 수 없습니다.'
		}, status=status.HTTP_404_NOT_FOUND)




class ErrorLog_ViewSet(viewsets.ModelViewSet):
	MODEL = ErrorLog
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.ErrorLogSerializer
	parser_classes = [MultiPartParser, FormParser]

	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]

	# filterset_class = Api_App사용자_FilterSet

	def get_queryset(self):
		return self.MODEL.objects.order_by('-id')

# class Portal_Info_ViewSet(viewsets.ModelViewSet):
# 	MODEL = Portal_Info
# 	queryset = MODEL.objects.order_by('order')
# 	serializer_class = serializers.Portal_Info_Serializer
# 	parser_classes = [MultiPartParser, FormParser]
# 	filter_backends = [
# 		filters.DjangoFilterBackend,
# 	]
# 	filterset_class = Portal_Info_FilterSet
# 	ordering_fields = ['order']
# 	ordering = ['order']


@api_view(['POST'])
@permission_classes([AllowAny])  # 관리자만 접근 가능
def login_in_portal(request):
	try:
		user_mailid = request.data.get('user_mailid')
		password = request.data.get('password')  # 초기 비밀번호 설정
		Util.print_debug('users', 'login_in_portal', f"user_mailid: {user_mailid} request to login_in_portal")
		user = authenticate(username=user_mailid, password=password)
		if user is None:
			return Response({
				'error': '인증이 되지 않았읍니다.'
			}, status=status.HTTP_404_NOT_FOUND)

		if user.is_admin:
			qs = Portal_Info.objects.all().order_by('order')
		else:
			qs = Portal_Info.objects.filter(
				portal_permission__user=user,
				portal_permission__is_active=True,
				is_active=True
			).distinct().order_by('order')

		refresh = RefreshToken.for_user(user)
		return Response({
			'tokens': {
				'refresh': str(refresh),
				'access': str(refresh.access_token),
			},
			'user_info': serializers.UserSerializer(user).data,
			'portal_info': serializers.Portal_Info_Serializer(qs, many=True).data
		}, status=status.HTTP_200_OK)

		
	except Exception as e:
		return Response({
			'error': f'오류가 발생했습니다.{str(e)}'
		}, status=status.HTTP_404_NOT_FOUND)