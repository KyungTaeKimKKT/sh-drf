"""
Views for the csvupload APIs
"""
import io, csv, pandas as pd
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
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from tqdm import tqdm
from django.db.models import Q
from util.base_model_viewset import BaseModelViewSet

from .models import (
	Csvupload,
	Elevator,
	Elevator_Summary_WO설치일,
	ISO3166_KR,
)


from . import serializers
from .customfilters import (
	# ElevatorFilter, 
	SummaryWO설치일Filter,
)

from util.customfilters import Elevator_Info_FilterSet, Elevator_승강기협회_FilterSet

import util.utils_func as Util
import copy


class 승강기협회_ViewSet(BaseModelViewSet):
	""" 승강기협회 view set for 조회"""   
	http_method_names = ['get', 'head', 'options'] 
	MODEL = Elevator
	APP_ID = 88
	APP_INFO = {'div':'Elevator_Info', 'name':'승강기협회'}
	APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
	use_cache = True
	use_cache_permission = False
	cache_base = "Elevator 승강기협회"
	cache_timeout = 60 * 60
	queryset = MODEL.objects.all()
	serializer_class = serializers.승강기협회_Serializer
	search_fields =['건물명', '건물주소'] 
	filterset_class = Elevator_승강기협회_FilterSet
	ordering_fields = ['건물명','건물주소', '시도','시군구','최초설치일자']
	ordering = ['건물명', '건물주소', ]

	cache_timeout = 60 * 60

	def get_queryset(self):
		return self.MODEL.objects.all()



class Summary_WO설치일_ViewSet(BaseModelViewSet):
	""" 엘러베이터 대수  view set for 조회"""   
	http_method_names = ['get', 'head', 'options'] 
	MODEL = Elevator_Summary_WO설치일
	APP_INFO = {'div':'Elevator_Info', 'name':'한국정보'}
	APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
	use_cache = True
	use_cache_permission = True
	queryset = MODEL.objects.all()
	serializer_class = serializers.Elevator_Summary_WO설치일_Serializer
	search_fields =['건물명', '건물주소',] 
	filterset_class = Elevator_Info_FilterSet
	ordering_fields = ['건물명','건물주소', '시도','시군구','최초설치일자']
	ordering = ['건물명', '건물주소', ]
	cache_base = "Elevator 한국정보"

	cache_timeout = 60 * 60

	def get_queryset(self):
		return self.MODEL.objects.all()


class CsvUploadViewSet(viewsets.ModelViewSet):
	"""View for manage Csvupload APIs."""
	serializer_class = serializers.CsvUpload_Serializer
	# serializer_class = serializers.RecipeDetailSerializer
	queryset = Csvupload.objects.all()
	parser_classes = [MultiPartParser]
	# authentication_classes = [TokenAuthentication]
	# permission_classes = [IsAuthenticated]

	def _params_to_ints(self, qs):
		"""Convert a list of strings to integers."""
		return [int(str_id) for str_id in qs.split(',')]
	
	@action(methods=["DELETE"], detail =False, )
	def delete(self, request:Request):
		# delete_id =request.data
		delete_all = self.queryset
		delete_all.delete()
		return Response( self.serializer_class(delete_all,many=True).data) 
	
@api_view( ['POST'])
def Summary_WO설치일_FileDownload(request):
	q_final = generate_Q(request)
	return generate_Response_from_Model_Q(
		MODEL=Elevator_Summary_WO설치일,
		Q_final= q_final,
		sheetName = '검색_download'
	)


@api_view( ['POST'])
def 승강기협회_FileDownload(request):
	q_final = generate_Q(request)
	return generate_Response_from_Model_Q(
		MODEL=Elevator,
		Q_final= q_final,
		sheetName = '검색_download'
	)



@api_view(['POST','DELETE'])
def 관리_Summary_WO설치일(request):
	# if request.method == 'GET':
	#     queryset = Elevator_Summary_WO설치일.objects.all()
	#     serializer = serializers.Elevator_Summary_WO설치일_Serializer(queryset, many=True)
	#     return JsonResponse(serializer.data, safe=False)
	
	if request.method == 'POST':
		queryset = Elevator.objects.order_by('건물명','건물주소', '시도','시군구','최초설치일자')

		pv_list = ['건물명','건물주소', '시도','시군구']
		df = pd.DataFrame ( list (queryset.values (*pv_list)))
		df2 = df.groupby(pv_list, as_index=False).agg(count=('건물명', "count"))
		df2.columns = pv_list+['수량']
		# df2 = df.groupby(['건물명','건물주소', '시도','시군구'], as_index=False).agg( {'수량':'sum'})

		pv_list = ['건물명','건물주소', '시도','시군구','최초설치일자','건물주소_찾기용','시도_ISO']
		df_merge대상 = pd.DataFrame ( list (queryset.values (*pv_list)))
		df_unique = df_merge대상.drop_duplicates(['건물명','건물주소'])

		final_df = df2.merge(df_unique[['건물명','건물주소','최초설치일자','건물주소_찾기용','시도_ISO']], on=['건물명','건물주소'], how='left')        
		# df2.reset_index()

		# !!!!  아래로 구동시 예상시간 6000 초 , 
		# !!!!  bulk create시, 27초
		# count = 0
		# stime = time.time()
		# fulllength = len(df2.to_dict(orient='records') )
		# for obj in df2.to_dict(orient='records'):
		#     count +=1
		#     if ( count % 1000 == 0) :
		#         esttime= time.time() - stime
		#         print ( '완료율: ', count / fulllength *100, ' %' , '----  예상종료시간 : ', esttime * fulllength / count )
			
		#     Elevator_Summary_WO설치일.objects.create(**obj)

		# https://stackoverflow.com/questions/34425607/how-to-write-a-pandas-dataframe-to-django-model
		# Not able to iterate directly over the DataFrame
		df_records = final_df.to_dict('records')
		model_instances = [Elevator_Summary_WO설치일(
			건물명 =record['건물명'],
			건물주소=record['건물주소'],
			건물주소_찾기용 = record['건물주소_찾기용'],
			시도 =record['시도'],
			시군구=record['시군구'],
			수량 = record['수량'],
			loc_x =0,
			loc_y = 0,
			# 시도_ISO = record['시도_ISO'],
			# 시도_ISO = ISO3166_KR.objects.get(name_for_elevator = record['시도']),
			최초설치일자 = record['최초설치일자'],
			
		) for record in tqdm(df_records)]

		Elevator_Summary_WO설치일.objects.bulk_create(model_instances)
		# print ( '----  소요시간 : ', time.time() - stime )

		return Response({'status': 200})

	if request.method == 'DELETE':
		Elevator_Summary_WO설치일.objects.all().delete()

		return Response({'status': 200})
	

### Utility functions
#####################
def generate_Q(request) -> Q:
	if ( search :=  request.data.get('search')):
		Q_search = Q( 건물명__contains = search) | Q( 건물주소__contains = search) 
	else:
		Q_search = Q()
	
	if ( 시도 := request.data.get('시도')):
		Q_시도 = Q( 시도__contains = 시도) 
	else:
		Q_시도 = Q() 

	if ( From수량 :=  request.data.get('From수량') ) and (  To수량 :=  request.data.get('To수량') ):
		Q_수량 = Q( 수량__lte=int(To수량) ) & Q(수량__gte = int(From수량) )
	else :
		Q_수량 = Q()
	from datetime  import datetime
	if ( From일자 :=  request.data.get('From일자')) and (  To일자 :=  request.data.get('To일자')):
		Q_최초설치일자 = Q( 최초설치일자__lte=datetime.strptime(To일자, '%Y-%m-%d').date() ) & Q(최초설치일자__gte = datetime.strptime(From일자, '%Y-%m-%d').date()  )
	else :
		Q_최초설치일자 = Q()
	return Q_search & Q_시도 & Q_최초설치일자 & Q_수량  
	
from django.db import models
from django.http import HttpResponse 

# @Util.timeit
# def generate_Response_from_Model_Q (MODEL:models.Model, Q_final: Q , sheetName) -> HttpResponse:    
#     qs = MODEL.objects.filter(Q_final)
#     import io, xlsxwriter
#     output = io.BytesIO()
#     df = pd.DataFrame(qs.values())
#     # df.to_excel( 'download.xlsx')
#     writer = pd.ExcelWriter(output,engine='xlsxwriter')
#     df.to_excel(writer,sheet_name=sheetName)
#     writer.close()
#     output.seek(0)
#     output_name = 'download'
#     from django.http import HttpResponse 
#     response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#     response['Content-Disposition'] = f'attachment; filename={output_name}.xlsx'
#     # df.to_excel(response)
#     return response



@Util.timeit
def generate_Response_from_Model_Q (MODEL:models.Model, Q_final: Q , sheetName) -> HttpResponse:    
	qs = MODEL.objects.filter(Q_final)
	import io, xlsxwriter, os
	# output = io.BytesIO()
	df = pd.DataFrame(qs.values())
	fName = 'download.xlsx'
	fName = Util.generate_Path()+ fName
	df.to_excel( fName, sheet_name=sheetName)
	return Response( data= {'fileName':  os.path.abspath(fName), 'fileSize': os.path.getsize(fName)}, status=status.HTTP_200_OK)

	output_name = 'download'
	from django.http import HttpResponse 
	# response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
	# response['Content-Disposition'] = f'attachment; filename={output_name}.xlsx'
	# df.to_excel(response)
	return response

