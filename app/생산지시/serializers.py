"""
Serializers for 생산지시
"""
from django.conf import settings
from rest_framework import serializers
from django.db.models import Sum
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5

from datetime import datetime, date,time, timedelta
import datetime as dt
import time
from django.utils import timezone

from users.models import Api_App권한, User
from . import models
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
		model = models.JAMB_file
		fields = '__all__'
		read_only_fields = ['id'] 

class JAMB_발주정보_Serializer(serializers.ModelSerializer, Serializer_m2m):
	class Meta:
		model = models.JAMB_발주정보
		fields = '__all__'
		# fields =[f.name for f in model._meta.fields] + [ 'JAMB_files_fks']
		read_only_fields = ['id'] 

	def to_representation(self, instance):
		response = super().to_representation(instance)
		# response['file1_fk'] = SPG_file_Serializer(instance.file1_fk).data
		# response['file2_fk'] = SPG_file_Serializer(instance.file2_fk).data
		return response


class TAB_Made_file_Serializer(serializers.ModelSerializer):

	class Meta:
		model = models.TAB_Made_file
		fields = '__all__'
		read_only_fields = ['id'] 


class SPG_file_Serializer(serializers.ModelSerializer):

	class Meta:
		model = models.SPG_file
		fields = '__all__'
		read_only_fields = ['id'] 


class 도면file_Serializer(serializers.ModelSerializer):

	class Meta:
		model = models.도면file
		fields = '__all__' 
		read_only_fields = ['id'] 

class 도면상세내용_Serializer(serializers.ModelSerializer):

	class Meta:
		model = models.도면상세내용
		fields = '__all__'
		read_only_fields = ['id'] 

class 도면정보_Serializer(serializers.ModelSerializer):
	# 상세내용_fks = 도면상세내용_Serializer(many=True, required=False)
	class Meta:
		model = models.도면정보
		fields = '__all__'
		read_only_fields = ['id'] 

class SPG_Table_Serializer(serializers.ModelSerializer):

	class Meta:
		model = models.SPG_Table
		fields = '__all__'
		read_only_fields = ['id'] 


class SPG_Serializer(serializers.ModelSerializer, Serializer_m2m):
	# spg_table_fks = SPG_Table_Serializer(many=True, required=False)
	# spg_table_fks_contents = serializers.SerializerMethodField(method_name='_get_spg_table_fks_contents')
	# file1_fk_contents = serializers.SerializerMethodField(method_name='_get_file1_fk_contents')
	# file2_fk_contents = serializers.SerializerMethodField(method_name='_get_file2_fk_contents')

	class Meta:
		model = models.SPG
		fields = '__all__'
		read_only_fields = ['id'] 

	def to_representation(self, instance:models.SPG):
		response = super().to_representation(instance)
		response['file1_URL'] = instance.file1_fk.file.url if bool(instance.file1_fk) else ''
		response['file2_URL'] = instance.file1_fk.file.url if bool(instance.file1_fk) else ''
		return response


class Process_Serializer(serializers.ModelSerializer):

	class Meta:
		model = models.Process
		fields = '__all__'
		read_only_fields = ['id'] 

class 생산지시_Serializer(serializers.ModelSerializer, Serializer_m2m):

	class Meta:
		model = models.생산지시
		fields = '__all__'
		read_only_fields = ['id'] 

	def to_representation(self, instance:models.생산지시):
		data = super().to_representation(instance)
		data['호기_수'] = instance.도면정보_fks.count() if instance.도면정보_fks else 0

		_filtered_HTM = instance.process_fks.exclude(적용__icontains='jamb')
		data['HTM_Sheet'] = _filtered_HTM.aggregate(Sum('수량'))['수량__sum'] or 0
		data['is_HTM_확정'] = _filtered_HTM.count() == _filtered_HTM.filter(확정=True).count()

		_filtered_JAMB = instance.process_fks.filter(적용__icontains='jamb')
		data['JAMB_Sheet'] = _filtered_JAMB.aggregate(Sum('수량'))['수량__sum'] or 0
		data['is_JAMB_확정'] = _filtered_JAMB.count() == _filtered_JAMB.filter(확정=True).count()

		data['상세의장수'] = len(set(
                                        ''.join(proc.상세Process.split()) # 모든 공백 문자 제거
                                        for proc in instance.process_fks.all()
                                        if '해당사항' not in ''.join(proc.상세Process.split())  # 공백이 제거된 상태로 비교
                                    ))
		if instance.도면정보_fks.all().count() > 0:
			data['납기일_Door'] = min( [ hogi.납기일_Door for hogi in instance.도면정보_fks.all() if hogi and hasattr( hogi, '납기일_Door' ) and hogi.납기일_Door ] )
			data['납기일_Cage'] = min( [ hogi.납기일_Cage for hogi in instance.도면정보_fks.all() if hogi and hasattr( hogi, '납기일_Cage' ) and hogi.납기일_Cage ] )
		else :
			data['납기일_Door'] = None
			data['납기일_Cage'] = None
		# data['JAMB_발주정보_fk'] = JAMB_발주정보_Serializer(instance.JAMB_발주정보_fk).data
		return data

    



# class 생산지시_결재_Serializer(생산지시_Serializer):

# 	def update(self, instance, validated_data):
		
# 		if ( self.결재내용_fks ):
# 			for 결재obj in self.결재내용_fks:
# 				for __instance in instance.결재내용_fks.all():
# 					print ( 결재obj )
# 					if ( __instance.id == 결재obj['id'] ):
# 						결재obj.pop('id')
# 						for attr, value in 결재obj.items():
# 							setattr( __instance, attr, value)
# 						__instance.save()
# 						break

# 		instance.진행현황 = self._get_진행현황(instance)
# 		instance.save()
# 		return instance


# 	def _get_inputFields(self, instance):
# 		print (self.fields)
# 		return self.fields
# 	# def _get_현장명_fk_full(self, instance):
# 	#     return False

# 	# def _get_group_의뢰차수(self, instance):
# 	#     return Group생산지시.objects.filter(group = instance.id ).count()
	
# 	def _get_첨부file수(self, instance):
# 		return instance.첨부file_fks.count()
	
# 	def _get_진행현황(self, instance):
# 		if ( not instance.결재내용_fks.count() ): return '작성중'
		
# 		for 결재instance in instance.결재내용_fks.all() :
# 			if ( 결재instance.결재결과 is not None ) :
# 				print ( 결재instance.결재결과, not 결재instance.결재결과)
# 				if( not 결재instance.결재결과 ): return '반려'

# 		for 결재instance in instance.결재내용_fks.all() :
# 			if ( 결재instance.결재결과 is None) : return '진행중'

# 		return '완료'        

# 	# def _get_접수디자이너_selector(self, instance):
# 	#     url = '/디자인관리/디자인관리_완료.html'
# 	#     obj = Api_App권한.objects.get(url=url)
# 	#     sel = ['None']
# 	#     for userObj in obj.user_pks.all():
# 	#         if 'admin' not in userObj.user_성명: sel.append(userObj.user_성명)
# 	#     return sel
