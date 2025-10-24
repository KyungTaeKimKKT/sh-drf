"""
Serializers for 생산지시
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
	SPG_file,
	도면file, 
	도면상세내용, 
	도면정보,
	Process,
	생산지시,
	SPG_Table,
	SPG,
	Group생산지시,
	TAB_Made_file,
	JAMB_file,
	JAMB_발주정보
	# 결재내용,
)
from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일
from elevator_info.serializers import Elevator_Summary_WO설치일_Serializer
from 작업지침.serializers import 작업지침_Serializer
from 품질경영.serializers import NCR_Serializer
from util.serializer_for_m2m import Serializer_m2m
import json


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

class JAMB_file_Serializer(serializers.ModelSerializer):
	class Meta:
		model = JAMB_file
		fields =[f.name for f in model._meta.fields] 
		read_only_fields = ['id'] 

class JAMB_발주정보_Serializer(serializers.ModelSerializer, Serializer_m2m):
	MODEL = JAMB_발주정보
	JAMB_files_fks = JAMB_file_Serializer(many=True, required=False)

	class Meta:
		model = JAMB_발주정보
		fields =[f.name for f in model._meta.fields] + [ 'JAMB_files_fks']
		read_only_fields = ['id'] 

	def __init__(self, *args, **kwargs):
		if ( fks:= kwargs.pop('fks', None) ):
			for key, value in fks.items():
				self.__setattr__(key, value)

		self.fks_ids = {
			"JAMB_files_fks" : JAMB_file,
		}
		# self.fks_files  = {
		#     "spg_file_fks" : SPG_file,
		# }

		super().__init__(*args, **kwargs)

	def to_representation(self, instance):
		response = super().to_representation(instance)
		# response['file1_fk'] = SPG_file_Serializer(instance.file1_fk).data
		# response['file2_fk'] = SPG_file_Serializer(instance.file2_fk).data
		return response

	def create(self, validated_data):
		instance = self.MODEL.objects.create(**validated_data)
		self._instanace_fks_manage(instance )

		instance.save()
		return instance
	
	def update(self, instance, validated_data):
		print ( "update내 validated-data :  최초 - ", validated_data )
		print ( '--------------------------------------\n\n\n')

		self._instanace_fks_manage(instance)  
		super().update(instance=instance, 
					   validated_data=self._update_validated_data(instance, validated_data))

		return self.MODEL.objects.get(id=instance.id)



class TAB_Made_file_Serializer(serializers.ModelSerializer):

	class Meta:
		model = TAB_Made_file
		fields =[f.name for f in TAB_Made_file._meta.fields] 
		read_only_fields = ['id'] 


class SPG_file_Serializer(serializers.ModelSerializer):

	class Meta:
		model = SPG_file
		fields =[f.name for f in SPG_file._meta.fields] 
		read_only_fields = ['id'] 


class 도면file_Serializer(serializers.ModelSerializer):

	class Meta:
		model = 도면file
		fields =[f.name for f in model._meta.fields] 
		read_only_fields = ['id'] 

class 도면상세내용_Serializer(serializers.ModelSerializer):

	class Meta:
		model = 도면상세내용
		fields =[f.name for f in model._meta.fields] 
		read_only_fields = ['id'] 

class 도면정보_Serializer(serializers.ModelSerializer):
	# 상세내용_fks = 도면상세내용_Serializer(many=True, required=False)
	class Meta:
		model = 도면정보
		fields =[f.name for f in model._meta.fields] 
		read_only_fields = ['id'] 

class SPG_Table_Serializer(serializers.ModelSerializer):

	class Meta:
		model = SPG_Table
		fields =[f.name for f in model._meta.fields] 
		read_only_fields = ['id'] 


class SPG_Serializer(serializers.ModelSerializer, Serializer_m2m):
	spg_table_fks = SPG_Table_Serializer(many=True, required=False)
	# spg_table_fks_contents = serializers.SerializerMethodField(method_name='_get_spg_table_fks_contents')
	# file1_fk_contents = serializers.SerializerMethodField(method_name='_get_file1_fk_contents')
	# file2_fk_contents = serializers.SerializerMethodField(method_name='_get_file2_fk_contents')

	class Meta:
		model = SPG
		extra_fields =  ['spg_table_fks', ] #'file1_fk_contents' ,'file2_fk_contents'] 
		fields =[f.name for f in model._meta.fields] + extra_fields
		read_only_fields = ['id'] 

	def __init__(self, *args, **kwargs):
		if ( fks:= kwargs.pop('fks', None) ):
			for key, value in fks.items():
				self.__setattr__(key, value)
		self.fks_ids = {
			"spg_table_fks" : SPG_Table,
		}
		# self.fks_files  = {
		#     "spg_file_fks" : SPG_file,
		# }

		super().__init__(*args, **kwargs)

	def to_representation(self, instance):
		response = super().to_representation(instance)
		response['file1_fk'] = SPG_file_Serializer(instance.file1_fk).data
		response['file2_fk'] = SPG_file_Serializer(instance.file2_fk).data
		return response
	
	def _get_spg_table_fks_contents(self, instance):
		if instance.spg_table_fks:
			return SPG_Table_Serializer(instance.spg_table_fks).data	

	def _get_file1_fk_contents(self, instance):
		if instance.file1_fk:
			return SPG_file_Serializer(instance.file1_fk).data	
		
	def _get_file2_fk_contents(self, instance):
		if instance.file2_fk:
			return SPG_file_Serializer(instance.file2_fk).data	

	def create(self, validated_data):
		instance = SPG.objects.create(**validated_data)
		self._instanace_fks_manage(instance )

		instance.save()
		return instance
	
	def update(self, instance, validated_data):
		self._instanace_fks_manage(instance)  
		super().update(instance=instance, 
					   validated_data=self._update_validated_data(instance, validated_data))

		return SPG.objects.get(id=instance.id)



class Process_Serializer(serializers.ModelSerializer):

	class Meta:
		model = Process
		fields =[f.name for f in model._meta.fields]
		read_only_fields = ['id'] 

class 생산지시_Serializer(serializers.ModelSerializer, Serializer_m2m):
	도면정보_fks = 도면정보_Serializer(many=True, required=False)
	process_fks = Process_Serializer(many=True, required=False)
	spg_fks = SPG_Serializer (many=True, required=False)
	tab_made_fks = TAB_Made_file_Serializer(many=True, required=False)

	작업지침_fk_contents= serializers.SerializerMethodField(method_name='_get_작업지침_fk_contents')
	JAMB_발주정보_fk_contents= serializers.SerializerMethodField(method_name='_get_JAMB_발주정보_fk_contents')

	# NCR_fk = NCR_Serializer


	class Meta:
		model = 생산지시
		extra_fields =  ['process_fks','도면정보_fks' ,'spg_fks','tab_made_fks', '작업지침_fk_contents','JAMB_발주정보_fk_contents'] 
		fields =[f.name for f in 생산지시._meta.fields] + extra_fields
		read_only_fields = ['id'] 
		validators = []  # Remove a default "unique together" constraint.

	def to_representation(self, instance):
		response = super().to_representation(instance)
		# response['JAMB_발주정보_fk'] = JAMB_발주정보_Serializer(instance.JAMB_발주정보_fk).data
		return response
	
	def _get_작업지침_fk_contents(self, instance):
		if instance.작업지침_fk:
			return 작업지침_Serializer(instance.작업지침_fk).data		 
	
	def _get_JAMB_발주정보_fk_contents(self, instance):
		if instance.JAMB_발주정보_fk:
			return JAMB_발주정보_Serializer(instance.JAMB_발주정보_fk).data
	

	def __init__(self, *args, **kwargs):
		if ( fks:= kwargs.pop('fks', None) ):
			for key, value in fks.items():
				self.__setattr__(key, value)

		# self.fks_json = {
		# 	"도면정보_fks" : 도면정보,
		# 	"process_fks" : Process,
		# }
		# self.fks_files  = {
		#     "spg_file_fks" : SPG_file,
		# }
		self.fks_ids = {
			"spg_fks" : SPG,
			"tab_made_fks" : TAB_Made_file,
			"도면정보_fks" : 도면정보,
			"process_fks" : Process,
		}

		super().__init__(*args, **kwargs)


	def create(self, validated_data):
		instance = 생산지시.objects.create(**validated_data)
		self._instanace_fks_manage(instance)

		instance.save()
		return instance


	def update(self, instance, validated_data):
		self._instanace_fks_manage(instance)  
		super().update(instance=instance, 
					   validated_data=self._update_validated_data(instance, validated_data))

		return 생산지시.objects.get(id=instance.id)


	# def _update_validated_data(self, instance, validated_data) :
	#     # validated_data['첨부파일수'] = instance.file_fks.count()
	#     return validated_data
	
	# def _instanace_fks_manage(self, instance:생산지시) ->None:
	#     ### m2m filed
	#     if hasattr(self, 'process_fks'):
	#         if ( self.process_fks):
	#             # print ( self.process_fks)
	#             instance.process_fks.clear()
	#             for process in self.process_fks:
	#                 instance.process_fks.add (self.m2m_create_or_update(process, Process))
	#     if hasattr(self, '도면정보_fks'):
	#         if ( self.도면정보_fks):
	#             # print ( self.도면정보_fks)
	#             instance.도면정보_fks.clear()
	#             for 도면정보_process in self.도면정보_fks:
	#                 instance.도면정보_fks.add (self.m2m_create_or_update(도면정보_process, 도면정보))

	#     # self.handle_m2m(instance, '첨부file_fks', 첨부file)
	#     # self.handle_m2m(instance, '완료file_fks', 완료file)

	# def handle_m2m(self, instance, m2m_field:str, Model) -> None:
	#     if ( instance_m2m := getattr(instance, m2m_field, None) ) is None: return

	#     if hasattr( self,  f"{m2m_field}_삭제"):
	#         if getattr(self, f"{m2m_field}_삭제") :
	#             instance_m2m.clear()
		
	#     if hasattr( self, f"{m2m_field}_json"):
	#         if (m2m_json:=  getattr(self, f"{m2m_field}_json" )):
	#              instance_m2m.set( m2m_json )

	#     if hasattr ( self, m2m_field):
	#         if (m2m := getattr(self, m2m_field) ) :
	#             for file in m2m:
	#                 instance_m2m.add( Model.objects.create(file=file))

	# def m2m_create_or_update(self, process:dict, Model) -> object:
	#     id = process.pop('id', -1)
	#     if isinstance(id, int) and id >0:
	#         Model.objects.filter(id = id).update(**process)
	#         return Model.objects.get(id=id)
	#     else :
	#         return  Model.objects.create(**process)
		

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



class 생산지시_결재_Serializer(생산지시_Serializer):

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

		instance.진행현황 = self._get_진행현황(instance)
		instance.save()
		return instance


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
