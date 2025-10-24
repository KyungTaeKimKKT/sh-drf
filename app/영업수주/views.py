"""
Views for the 영업수주 APIs
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
# from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from django.db import models
import django_rq
import pickle, hashlib, os
from rest_framework.parsers import MultiPartParser,FormParser
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
# from datetime import datetime, date,time, timedelta
import datetime, time
from django.http import QueryDict
import json
import pandas as pd
from django.utils.dateparse import parse_date, parse_datetime
from django.db import transaction
from django.db.models import Q, F
from itertools import groupby
from operator import itemgetter
import copy
from django.core.cache import cache
import multiprocessing as mp
from collections import defaultdict

from . import models as 영업수주Models
from . import serializers as 영업수주Serializers
from . import signal as 영업수주Signal
# from . import customfilters
import logging
import 생산지시.models as 생산지시Models
from serial.models import SerialHistory  # SerialHistory 모델 import 추가

### tasks.py 추가
from 영업수주.tasks import preprocess_excel_file

import util.utils_func as utils
from util.utils_viewset import Util_Model_Viewset
from util.customfilters import 생산지시_DB_FilterSet
from util.excelreader import ExcelReader
from util.websocketmessagesender import WebSocketMessageSender


# 클래스 외부에 전역 함수로 정의
def get_관리_인스턴스_id(args):
    """관리 인스턴스 추출 (전역 함수)"""
    호기번호, shared_dict = args
    if 호기번호 and shared_dict:
        return shared_dict.get(호기번호)
    return None

def get_의장_인스턴스_id(args):
    """의장 인스턴스 추출 (전역 함수)"""
    자재내역, shared_dict = args
    if 자재내역 and shared_dict:
        for _keywords, _id in shared_dict.items():
            keywordSet = set(map(str.strip, _keywords.split(',')))
            if all([keyword in 자재내역 for keyword in keywordSet]):
                return _id
    return None




class 영업수주_프로세서_기본:
    """영업수주 처리를 위한 기본 클래스"""
    
    def __init__(self, 관리_obj, ws_sender, MODEL:models.Model|None=None):
        self.관리_obj = 관리_obj
        self.ws_sender = ws_sender
        self.error_logs = []
        self.created_count = 0
        self.bulk_create_data = []
        self.MODEL = MODEL
        self.model_fields = self._get_model_fields()
        self.df:pd.DataFrame|None = None

    def _get_model_fields(self):
        """모델 필드 추출"""
        return {field.name: field for field in self.MODEL._meta.get_fields() if field.name != 'id' and field.concrete }
    
    def process(self):
        """Process 함수 구현( 하위 클래스에서 구현 )"""
        raise NotImplementedError
    
    def _read_excel(self):
        """Excel 파일 읽기 (하위 클래스에서 구현)"""
        raise NotImplementedError
    
    def _preprocess_data(self):
        """데이터 전처리 (하위 클래스에서 구현)"""
        raise NotImplementedError
    
    def _save_to_database(self):
        """데이터베이스에 저장 (하위 클래스에서 구현)"""
        raise NotImplementedError
    
    def _get_batch_size(self, data_list):
        """배치 크기 결정"""
        if len(data_list) <= 5000:
            return len(data_list)
        elif len(data_list) <= 100000:
            return 5000
        else:
            return 5000


class 영업수주_일정_프로세서(영업수주_프로세서_기본):
    """영업수주 일정 처리 클래스"""
    
    def __init__(self, 관리_obj, ws_sender, MODEL:models.Model|None=None):
        super().__init__(관리_obj, ws_sender, MODEL)
        self.날짜fields = [
            '기계실_출하요청일', '구조물_출하요청일', '출입구_출하요청일', 'DOOR_출하요청일', 
            'CAGE_출하요청일', '바닥재_출하요청일', '착공일', '설치투입일', '준공예정일', '준공일'
        ]
        self.관리_obj:영업수주Models.영업수주_관리 = 관리_obj

    def process(self):
        """Process 함수 구현"""

        try:
            self.ws_sender.subject("일정").sub_subject("Excel reading").message("excel 읽기 시작").progress(0).send()
            self._read_excel()
            self.ws_sender.subject("일정").sub_subject("Data 처리").message(f" {self.df.shape[0]}건 데이터 전처리 시작").progress(10).send()
            self._df_처리()
            self.ws_sender.subject("일정").sub_subject("DB 저장").message(f" {self.df.shape[0]}건 데이터 db 저장 시작").progress(20).send()
            self._save_to_database()
            # self.ws_sender.subject("일정").sub_subject("완료").message(f" {self.df.shape[0]}건 데이터 db 저장 완료").progress(30).send()
            
            return {
                'success': True,
                'created_count': self.created_count,
                'error_logs': self.error_logs
            }
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"처리 중 오류 발생: {e}")
            print(f"상세 오류: {error_traceback}")
            return {
                'error': str(e),
                'traceback': error_traceback
            }
    
    def _read_excel(self):
        """일정 Excel 파일 읽기"""
        try:
            # ExcelReader 클래스 사용
            reader = ExcelReader(self.관리_obj.일정file, use_cache=True, cache_key_prefix="일정파일")
            self.df = reader.read()
        except Exception as e:
            raise Exception(f"Excel 파일 읽기 오류: {str(e)}")
    
    def _update_model_fields(self):
        """모델 필드 업데이트"""
        _model_fields = copy.deepcopy(self.model_fields)
        for field in ['created_at', 'updated_at','id']:
            try:
                del _model_fields[field]
            except KeyError:
                pass
        _model_fields['관리_fk_id'] = None
        return _model_fields

    def _df_처리(self, df:pd.DataFrame|None=None):
        """df 처리"""
        self.df = df or self.df
        self.수정된_model_fields = self._update_model_fields()

        for col, field in self.수정된_model_fields.items():
            if isinstance(field, models.DateField) or isinstance(field, models.DateTimeField):
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                # NaT 값을 None으로 변환
                self.df[col] = self.df[col].where(~pd.isna(self.df[col]), None)

            elif isinstance(field, models.IntegerField):
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            elif isinstance(field, models.FloatField):
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                self.df[col] = self.df[col].fillna(0)
            elif isinstance(field, models.TextField):
                self.df[col] = self.df[col].astype(str)
                self.df[col] = self.df[col].fillna('')
            elif isinstance(field, models.BooleanField):
                self.df[col] = self.df[col].astype(bool)
                self.df[col] = self.df[col].fillna(False)
            elif isinstance(field, models.CharField):
                self.df[col] = self.df[col].astype(str)
                self.df[col] = self.df[col].fillna('')
            elif isinstance(field, models.DecimalField):
                self.df[col] = self.df[col].astype(float)
                self.df[col] = self.df[col].fillna(0)
            # elif isinstance(filed, models.ForeignKey):
            #     if col == '호기번호':
            #         self.df[col] = self._get_일정_인스턴스(self.df[col])
            #     else:
            #         self.df[col] = self.df[col].astype(int) 
        
        ### 관리_fk 처리
        self.df['관리_fk_id'] = self.관리_obj.id
  

    def _generate_instanceList(self, df):
        """인스턴스 생성을 위한 데이터 준비"""

        instance_list = [
            self.MODEL(**self._convert_row_to_dict(row)) for _, row in df.iterrows()
        ]
        return instance_list

    def _convert_row_to_dict( self, row:pd.Series ):
        """인스턴스 생성을 위한 데이터 준비"""
        _dict = {}
        # print ( self.updated_model_fields )
        # print ( self.df.columns )
        for fieldName in self.df.columns:
            if fieldName in self.수정된_model_fields:
                if pd.isna(row[fieldName]):
                    _dict[fieldName] = None
                else:
                    _dict[fieldName] = row[fieldName] if row[fieldName] !='nan' else None
        return _dict

    
    def _preprocess_data(self):
        """일정 데이터 전처리"""
        # 일정 데이터는 특별한 전처리가 필요 없음
        pass
    
    def _save_to_database(self, start_progress:int|None=None, end_progress:int|None=None):
        """일정 데이터를 데이터베이스에 저장"""
        instance_list = self._generate_instanceList(self.df)
        batch_size = self._get_batch_size(instance_list)
        if start_progress is not None and end_progress is not None:
            progress_range = end_progress - start_progress
        else:
            progress_range = None

        self.MODEL.objects.filter(관리_fk=self.관리_obj).delete()

        with transaction.atomic():
            for i in range( 0, len(instance_list), batch_size):
                batch_data = instance_list[i:i+batch_size]
                try:
                    self.MODEL.objects.bulk_create(batch_data, batch_size=batch_size)

                    if progress_range is not None:
                        # 진행률 계산 (start_progress에서 end_progress까지)
                        current_progress = min(i + batch_size, len(instance_list))
                        progress_percent = int(current_progress / len(instance_list) * progress_range) + start_progress
                
                        self.ws_sender \
                            .subject("일정") \
                            .sub_subject("DB 저장") \
                            .message(f"데이터 저장 완료: {i+batch_size}건") \
                            .progress(progress_percent) \
                            .send()
                except Exception as e:
                    print(f"배치 생성 중 오류 발생: {e}")
                    raise Exception(f"배치 생성 중 오류 발생: {e}")




class 영업수주_금액_프로세서(영업수주_프로세서_기본):
    """영업수주 금액 처리 클래스"""
    
    def __init__(self, 관리_obj, ws_sender, MODEL:models.Model|None=None):
        super().__init__(관리_obj, ws_sender, MODEL)
        self.날짜fields = [
            '납품예정일', '최초입력일자', '변경일자', '입고예정일', '변경납기일', '최초납기일',
            '생산계획일', '생산계획변경일', 'JAMB_실측일', '출하일자'
        ]
        self.날짜fields_datetime = ['납기일변경일시', '특성치변경일시', '발주승인일시', '발주삭제일시']
        self.numeric_columns = ['발주단가', '발주수량', '금액', '발주잔량', '신우_단가', '신우_실제금액', '현장대수']
        self.prev호기 = None
        self.prevInstance일정 = None

        self._usecols = [
            '발주번호', 'Proj_번호', '공사_현장명', '자재번호', '자재내역', '호기번호_WBS', '단위',
            '발주단가', '발주수량', '금액', '발주잔량', '신우_단가', '신우_실제금액', '도면번호',
            '현장대수', '변경납기일', '최초납기일', '생산계획일', '설치협력사', '출하일자', '공사주석', '거래명세서번호'
        ]
        self._dtype = {
            '발주번호': str, 'Proj_번호': str, '공사_현장명': str, '자재번호': str, '자재내역': str,
            '호기번호_WBS': str, '단위': str, '발주번호': str, 
            '도면번호': str, '현장대수': str, '변경납기일': str,
            '최초납기일': str, '생산계획일': str, '설치협력사': str, '출하일자': str, '공사주석': str,
            '거래명세서번호': str
        }

        self.관리_obj:영업수주Models.영업수주_관리 = 관리_obj
        # self._의장_dict:dict = {}
        # self._일정_instance_dict:dict[str:int] = {}    #### '호기번호': 일정_instance.id 형태
        # self.df_일정:pd.DataFrame|None = None       #### 일정 db를 읽어 df로 저장할 때 사용
        
    def process(self):
        """Process 함수 구현"""

        try:
            self.ws_sender.subject("금액").sub_subject("Excel reading").message("excel 읽기 시작").progress(30).send()
            s = time.time()
            self._read_excel()
            print ( f'excel 읽기 소요시간: {time.time() - s}' )
            self.ws_sender.subject("금액").sub_subject("Data 처리").message(f" {self.df.shape[0]}건 데이터 전처리 시작").progress(40).send()
            self._df_처리()
            self._df_후처리_single()
            # self._df_후처리_multi()       ### mp 생성비용이 더 큼 .. 여기선 거의 20배
            self.ws_sender.subject("금액").sub_subject("DB 저장").message(f" {self.df.shape[0]}건 데이터 db 저장 시작").progress(50).send()

            # 중요: 데이터베이스 저장 전에 기존 데이터 삭제
            self.MODEL.objects.filter(관리_fk=self.관리_obj).delete()
            self._save_to_database(start_progress=50, end_progress=80)
            # self.ws_sender.subject("금액").sub_subject("완료").message(f" {self.df.shape[0]}건 데이터 db 저장 완료").progress(80).send()
            self.ws_sender.subject("검증").sub_subject("검증결과").message(f"검증시작").progress(80).send()
            # 검증 실행
            validation_results = self.validate_data()

            # 검증 결과 요약
            total_issues = sum(len(items) for items in validation_results.values())
            if total_issues > 0:
                # 문제가 있는 경우 파일 생성
                file_paths = self.create_validation_files(validation_results)
                

                
                # 파일 전송
                for file_type, file_path in file_paths.items():
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                        file_name = os.path.basename(file_path)
                        
                        # 파일 타입에 따라 적절한 제목 설정
                        if file_type == 'txt':
                            subject = "검증 결과 종합"
                        elif '일정' in file_type:
                            subject = "일정 없음 항목"
                        elif '금액' in file_type:
                            subject = "금액 문제 항목"
                        elif '의장' in file_type:
                            subject = "의장 없음 항목"
                        else:
                            subject = "검증 결과"

                # 웹소켓으로 요약 메시지 전송
                self.ws_sender.subject("검증").sub_subject("검증결과").message(
                    f"검증 완료: 총 {total_issues}개 문제 발견\n"
                    f"- 일정 없음: {len(validation_results['일정_fk_없음'])}건\n"
                    f"- 금액 문제: {len(validation_results['금액_문제'])}건\n"
                    f"- 의장 없음: {len(validation_results['의장_fk_없음'])}건\n\n"
                    f"상세 결과는 첨부 파일을 확인하세요."
                ).file(file_name, file_content).progress(100).send()
  
                # 임시 파일 정리
                for file_path in file_paths.values():
                    try:
                        os.remove(file_path)
                    except:
                        pass
                try:
                    os.rmdir(os.path.dirname(list(file_paths.values())[0]))
                except:
                    pass
            else:
                # 문제가 없는 경우
                self.ws_sender.subject("검증").sub_subject("검증결과").message("검증 완료: 모든 데이터가 정상입니다.").progress(100).send()


            return {
                'success': True,
                'created_count': self.created_count,
                'error_logs': self.error_logs
            }
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"처리 중 오류 발생: {e}")
            print(f"상세 오류: {error_traceback}")
            return {
                'error': str(e),
                'traceback': error_traceback
            }
        

    
    def _read_excel(self) -> pd.DataFrame:
        """금액 Excel 파일 읽기"""
        try:
            # ExcelReader 클래스 사용
            reader = ExcelReader(
                self.관리_obj.금액file, 
                usecols=self._usecols, 
                dtype=self._dtype,
                use_cache=True, 
                cache_key_prefix="금액파일"
            )
            self.df = reader.read()
            # 숫자 컬럼 처리
            self.df = ExcelReader.process_numeric_columns(self.df, self.numeric_columns)
                
        except Exception as e:
            raise Exception(f"Excel 파일 읽기 오류: {str(e)}")
    

    def _update_model_fields(self):
        """모델 필드 업데이트"""
        _model_fields = copy.deepcopy(self.model_fields)
        for field in ['created_at', 'updated_at','id']:
            try:
                del _model_fields[field]
            except KeyError:
                pass
        _model_fields['호기번호'] = None
        _model_fields['관리_fk_id'] = None
        _model_fields['일정_fk_id'] = None
        _model_fields['의장_fk_id'] = None
        return _model_fields

    def _df_처리(self, df:pd.DataFrame|None=None):
        """df 처리"""
        self.df = df or self.df
        self.수정된_model_fields = self._update_model_fields()
        ### 호기번호 생성   
        self.df['호기번호'] = self.df['호기번호_WBS'].apply(lambda x: x.split('-')[0]).fillna('').astype(str)

        ### 데이터 정제
        for col, field in self.수정된_model_fields.items():
            if col in ['created_at', 'updated_at']:
                continue

            if isinstance(field, models.DateField) or isinstance(field, models.DateTimeField):
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
              # NaT 값을 None으로 변환
                self.df[col] = self.df[col].where(~pd.isna(self.df[col]), None)
            elif isinstance(field, models.IntegerField):
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            elif isinstance(field, models.FloatField):
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                self.df[col] = self.df[col].fillna(0)
            elif isinstance(field, models.TextField):
                self.df[col] = self.df[col].astype(str)
                self.df[col] = self.df[col].fillna('')
            elif isinstance(field, models.BooleanField):
                self.df[col] = self.df[col].astype(bool)
                self.df[col] = self.df[col].fillna(False)
            elif isinstance(field, models.CharField):
                self.df[col] = self.df[col].astype(str)
                self.df[col] = self.df[col].fillna('')
            elif isinstance(field, models.DecimalField):
                self.df[col] = self.df[col].astype(float)
                self.df[col] = self.df[col].fillna(0)
            # elif isinstance(filed, models.ForeignKey):
            #     if col == '호기번호':
            #         self.df[col] = self._get_일정_인스턴스(self.df[col])
            #     else:
            #         self.df[col] = self.df[col].astype(int) 
        
    def _df_후처리_single(self):
        """df 후처리"""
        ### 1.관리_fk_id 처리
        s= time.time()
        self.df['관리_fk_id'] = self.관리_obj.id
        print(f'관리_fk_id 처리 소요시간: {time.time() - s}')

        ### 2.일정_fk_id 처리
        s= time.time()
        
        _일정_instance_dict = { _dict['호기번호']: _dict['id'] 
                for _dict in 영업수주Models.영업수주_일정.objects.filter(관리_fk=self.관리_obj).values('id', '호기번호') }
        
        # 멀티프로세싱 대신 직접 매핑 처리
        self.df['일정_fk_id'] = self.df['호기번호'].map(_일정_instance_dict)
        
        print(f'일정_fk_id 처리 소요시간: {time.time() - s}')

        ### 3. 의장_fk_id 처리
        s= time.time()
        _의장_dict = { _dict['자재내역']: _dict['id'] 
                for _dict in 영업수주Models.자재내역_To_의장_Mapping.objects.all().values('id', '자재내역') }
        
        # 멀티프로세싱 대신 직접 처리
        def get_의장_id(자재내역):
            if 자재내역:
                for _keywords, _id in _의장_dict.items():
                    keywordSet = set(map(str.strip, _keywords.split(',')))
                    if all([keyword in 자재내역 for keyword in keywordSet]):
                        return _id
            return None
        
        self.df['의장_fk_id'] = self.df['자재내역'].apply(get_의장_id)
        
        print(f'의장_fk_id 처리 소요시간: {time.time() - s}')

    def _df_후처리_multi(self):
        """df 후처리"""
                ### 1.관리_fk_id 처리
        s= time.time()
        self.df['관리_fk_id'] = self.관리_obj.id
        print ( f'관리_fk_id 처리 소요시간: {time.time() - s}' )

        ### 2.일정_fk_id 처리
        s= time.time()
        
        _일정_instance_dict = { _dict['호기번호']: _dict['id'] 
                for _dict  in 영업수주Models.영업수주_일정.objects.filter(관리_fk=self.관리_obj).values('id', '호기번호') }
        ### 공유 가능한 Manager.dict 생성
        shared_dict = mp.Manager().dict(_일정_instance_dict)
        # 인자 리스트 생성 (호기번호와 shared_dict를 함께 전달)
        args_list = [(호기번호, shared_dict) for 호기번호 in self.df['호기번호']]
        with mp.Pool(mp.cpu_count()) as pool:
            self.df['일정_fk_id'] = pool.map(get_관리_인스턴스_id, args_list)
        
        print ( f'일정_fk_id 처리 소요시간: {time.time() - s}' )

        ### 3. 의장_fk_id 처리
        s= time.time()
        _의장_dict = { _dict['자재내역']: _dict['id'] 
                for _dict  in 영업수주Models.자재내역_To_의장_Mapping.objects.all().values('id', '자재내역') }
        shared_dict = mp.Manager().dict( _의장_dict )
        # 인자 리스트 생성
        args_list = [(자재내역, shared_dict) for 자재내역 in self.df['자재내역']]

        with mp.Pool(mp.cpu_count()) as pool:
            self.df['의장_fk_id'] = pool.map(get_의장_인스턴스_id, args_list)
        print ( f'의장_fk_id 처리 소요시간: {time.time() - s}' )


    def _generate_instanceList(self, df):
        """인스턴스 생성을 위한 데이터 준비"""
        instance_list = [
            self.MODEL(**self._convert_row_to_dict(row)) for _, row in df.iterrows()
        ]
        return instance_list

    def _get_일정_인스턴스_id(self, 호기번호:str|None=None) -> int|None:
        """일정 인스턴스 추출"""
        if 호기번호 and self.shared_dict:
            return self.shared_dict.get(호기번호)
        return None

    def _convert_row_to_dict( self, row:pd.Series ):
        """인스턴스 생성을 위한 데이터 준비"""
        _dict = {}
        for fieldName in self.df.columns:
            if fieldName in self.수정된_model_fields:
                if pd.isna(row[fieldName]):
                    _dict[fieldName] = None
                else:
                    _dict[fieldName] = row[fieldName] if row[fieldName] !='nan' else None
                
        return _dict

    def _preprocess_data(self):
        """금액 데이터 전처리"""
        # 숫자 컬럼 처리 - 콤마 제거 및 정수 변환
        for col in self.numeric_columns:
            if col in self.df.columns:
                # 콤마 제거, 소수점 제거하고 정수로 변환
                self.df[col] = self.df[col].apply(lambda x: 
                    int(float(str(x).replace(',', ''))) if pd.notna(x) and str(x).strip() != '' else None)
        
        self._dictList = self.df.to_dict(orient='records')
        # 처리할 데이터 제한 (필요시 페이징 처리로 확장 가능)
        self.targetList = self._dictList[:5000]
        print(f"bulk create dict 시작: {datetime.datetime.now()}, 처리할 데이터 개수: {len(self.targetList)}")
    

    def _save_to_database(self, start_progress:int|None=None, end_progress:int|None=None):
        """instance_list를  데이터베이스에 저장"""
        instance_list = self._generate_instanceList(self.df)
        batch_size = self._get_batch_size(instance_list)
        total_batches = (len(instance_list) + batch_size - 1) // batch_size
        if start_progress is not None and end_progress is not None:
            progress_range = end_progress - start_progress
        else:
            progress_range = 100
        s= time.time()
        with transaction.atomic():
            for i in range( 0, len(instance_list), batch_size):
                batch_data = instance_list[i:i+batch_size]
                batch_number = i // batch_size + 1
                try:
                    self.MODEL.objects.bulk_create(batch_data, batch_size=batch_size)
                    elapsed_time = time.time() - s
                    if progress_range is not None:
                        progress_percent = int( (i+batch_size)/len(instance_list)*progress_range ) + start_progress
                        self.ws_sender.subject("금액") \
                            .sub_subject("DB 저장") \
                            .message(f"데이터 저장 진행: {batch_number}/{total_batches} 배치 완료 ({progress_percent}%)") \
                            .progress(progress_percent) \
                            .send()

                    print(f"배치 {batch_number}/{total_batches}: {len(batch_data)}건 처리 완료 (누적 소요시간: {elapsed_time:.2f}초)")

                except Exception as e:
                    print(f"배치 생성 중 오류 발생: {e}")
                    raise Exception(f"배치 생성 중 오류 발생: {e}")
        total_time = time.time() - s
        print(f"전체 데이터 {len(instance_list)}건 저장 완료 (총 소요시간: {total_time:.2f}초)")
        _db_count = self.MODEL.objects.filter(관리_fk=self.관리_obj).count()
        print ( 'DB Record 확인 : { _db_count == len(instance_list) }', _db_count , len(instance_list) )
    
    def _clean_dict_data(self, data_dict, idx):
        """금액 딕셔너리 데이터 정제"""
        cleaned_dict = {}
        
        for key, value in data_dict.items():
            if pd.isna(value):
                cleaned_dict[key] = None
            elif key in self.날짜fields and value is not None:
                # 날짜 형식 변환 시도
                try:
                    if isinstance(value, str):
                        cleaned_dict[key] = parse_date(value)
                    else:
                        cleaned_dict[key] = value
                except Exception as date_error:
                    print(f"날짜 변환 오류 ({key}): {value}, 오류: {date_error}")
                    cleaned_dict[key] = None
            elif key in self.날짜fields_datetime and value is not None:
                # Datetime 변환 시도
                try:
                    if isinstance(value, str):
                        cleaned_dict[key] = parse_datetime(value)
                    else:
                        cleaned_dict[key] = value
                except Exception as date_error:
                    print(f"Datetime 변환 오류 ({key}): {value}, 오류: {date_error}")
                    cleaned_dict[key] = None
            else:
                # 문자열 필드의 길이 제한 처리
                if isinstance(value, str) and len(value) > 250:
                    if key == '공사주석':  # textfield라서 모두 저장
                        cleaned_dict[key] = value
                    else:
                        # 문자열이 너무 길면 자르고 로그에 기록
                        original_value = value
                        value = value[:250]
                        error_message = f"행 {idx+1}: 필드 '{key}'의 값이 너무 깁니다. 원본 길이: {len(original_value)}자, 250자로 잘랐습니다."
                        self.error_logs.append(error_message)
                
                cleaned_dict[key] = value
        
        return cleaned_dict
    
    def _process_호기번호(self, cleaned_dict, idx):
        """호기번호 처리 및 일정 객체 연결"""
        cleaned_dict['호기번호'] = cleaned_dict['호기번호_WBS'].split('-')[0]
        
        if self.prev호기 != cleaned_dict['호기번호']:
            currentInstance일정 = self.QS_일정.filter(호기번호=cleaned_dict['호기번호']).first()
            self.prev호기 = cleaned_dict['호기번호']
            self.prevInstance일정 = currentInstance일정
        else:
            currentInstance일정 = self.prevInstance일정
        
        cleaned_dict['일정_fk'] = currentInstance일정
        
        if not currentInstance일정:
            error_message = f"행 {idx+1}: 호기번호 {cleaned_dict['호기번호']}에 해당하는 일정이 없습니다."
            self.error_logs.append(error_message)
        
        return cleaned_dict
    
    def _process_의장_mapping(self, cleaned_dict):
        """자재내역을 기반으로 의장 매핑 처리"""
        for 의장_obj in self.QS_자재내역_To_의장_Mapping:
            if 의장_obj.자재내역 in cleaned_dict['자재내역']:
                cleaned_dict['의장_fk'] = 의장_obj
                break
        
        return cleaned_dict
    
     # 검증 로직 추가
    def validate_data(self):
        validation_results = {
            '일정_fk_없음': [],
            '금액_문제': [],
            '의장_fk_없음': []
        }
        
        # 데이터베이스에서 영업수주_금액 데이터 조회
        금액_데이터 = self.MODEL.objects.filter(관리_fk=self.관리_obj).select_related('일정_fk', '의장_fk')
        
        # 엑셀 파일의 원본 데이터 가져오기 (호기번호_WBS와 행 번호 매핑)
        reader = ExcelReader(
            self.관리_obj.금액file, 
            usecols=['호기번호_WBS', '자재내역', '신우_단가', '신우_실제금액'],
            use_cache=True, 
            cache_key_prefix="금액파일_검증"
        )
        excel_df = reader.read()
        excel_df['row_no'] = excel_df.index + 2  # 엑셀은 1부터 시작, 헤더 행 고려하여 +2
        
        # 1. 일정_fk가 없는 항목 검증
        print('일정 check')
        self.ws_sender.subject("검증").sub_subject("검증결과").message('일정 check').progress(83).send()
        일정없는_항목_list = 금액_데이터.filter(일정_fk__isnull=True).values_list('호기번호', flat=True)

        print ( '일정없는_항목 :', 일정없는_항목_list.count() )
        unique_일정없는_항목_list = list(set(일정없는_항목_list))

        
        # 2. 신우_단가 및 신우_실제금액 검증
        print('금액 check')
        self.ws_sender.subject("검증").sub_subject("검증결과").message('금액 check').progress(86).send()
        금액_문제_항목 = 금액_데이터.filter(
            models.Q(신우_단가__isnull=True) | 
            models.Q(신우_단가=0) |
            models.Q(신우_실제금액__isnull=True) | 
            models.Q(신우_실제금액=0)
        ).values_list('호기번호', flat=True)
        print ( '금액_문제_항목 :', 금액_문제_항목.count() )
        unique_금액_문제_항목_list = list(set(금액_문제_항목))
        
        # 3. 의장_fk가 없는 항목 검증
        print('의장 check')
        self.ws_sender.subject("검증").sub_subject("검증결과").message('의장 check').progress(89).send()        
        의장없는_항목_list = 금액_데이터.filter(의장_fk__isnull=True).values_list('호기번호', flat=True)
        print ( '의장없는_항목 :', 의장없는_항목_list.count() )
        unique_의장없는_항목_list = list(set(의장없는_항목_list))

        print ( 'chekc 완료')
        validation_results['일정_fk_없음'] = unique_일정없는_항목_list
        validation_results['금액_문제'] = unique_금액_문제_항목_list
        validation_results['의장_fk_없음'] = unique_의장없는_항목_list
        return validation_results

    def create_validation_files(self, validation_results):
        import csv
        import os
        import tempfile
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_paths = {}
        
        # 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp()
        
        # 텍스트 파일 생성
        txt_path = os.path.join(temp_dir, f"validation_results_{timestamp}.txt")
        with open(txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(f"영업수주 검증 결과 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 1. 일정_fk 없음
            txt_file.write(f"1. 일정_fk 없음 ({len(validation_results['일정_fk_없음'])}건)\n")
            txt_file.write("-" * 50 + "\n")
            for item in validation_results['일정_fk_없음']:
                # 문자열로 처리
                txt_file.write(f"호기번호: {item}\n")
            txt_file.write("\n")
            
            # 2. 금액 문제
            txt_file.write(f"2. 금액 문제 ({len(validation_results['금액_문제'])}건)\n")
            txt_file.write("-" * 50 + "\n")
            for item in validation_results['금액_문제']:
                # 문자열로 처리
                txt_file.write(f"호기번호: {item}\n")
            txt_file.write("\n")
            
            # 3. 의장_fk 없음
            txt_file.write(f"3. 의장_fk 없음 ({len(validation_results['의장_fk_없음'])}건)\n")
            txt_file.write("-" * 50 + "\n")
            for item in validation_results['의장_fk_없음']:
                # 문자열로 처리
                txt_file.write(f"호기번호: {item}\n")
        
        file_paths['txt'] = txt_path
        
        # CSV 파일 생성
        # 1. 일정_fk 없음
        # if validation_results['일정_fk_없음']:
        #     csv_path = os.path.join(temp_dir, f"일정_fk_없음_{timestamp}.csv")
        #     with open(csv_path, 'w', encoding='utf-8-sig', newline='') as csv_file:
        #         writer = csv.writer(csv_file)
        #         writer.writerow(['행 번호', '호기번호_WBS', '호기번호'])
        #         for item in validation_results['일정_fk_없음']:
        #             writer.writerow([item['row_no'], item['호기번호_WBS'], item['호기번호']])
        #     file_paths['일정_fk_없음_csv'] = csv_path
        
        # # 2. 금액 문제
        # if validation_results['금액_문제']:
        #     csv_path = os.path.join(temp_dir, f"금액_문제_{timestamp}.csv")
        #     with open(csv_path, 'w', encoding='utf-8-sig', newline='') as csv_file:
        #         writer = csv.writer(csv_file)
        #         writer.writerow(['행 번호', '호기번호_WBS', '신우_단가', '신우_실제금액'])
        #         for item in validation_results['금액_문제']:
        #             writer.writerow([item['row_no'], item['호기번호_WBS'], item['신우_단가'], item['신우_실제금액']])
        #     file_paths['금액_문제_csv'] = csv_path
        
        # # 3. 의장_fk 없음
        # if validation_results['의장_fk_없음']:
        #     csv_path = os.path.join(temp_dir, f"의장_fk_없음_{timestamp}.csv")
        #     with open(csv_path, 'w', encoding='utf-8-sig', newline='') as csv_file:
        #         writer = csv.writer(csv_file)
        #         writer.writerow(['행 번호', '호기번호_WBS', '자재내역'])
        #         for item in validation_results['의장_fk_없음']:
        #             writer.writerow([item['row_no'], item['호기번호_WBS'], item['자재내역']])
        #     file_paths['의장_fk_없음_csv'] = csv_path
        
        return file_paths
    
class 영업수주_Summary_Api(APIView):
    MODEL = 영업수주Models.영업수주_금액

    def _init_res_dict(self):
        fields_model = {'Proj_번호':'CharField', '호기번호':'CharField', '신우_실제금액':'IntegerField', 'DOOR_출하요청일':'DateField', 
                    '의장_fk__의장':'CharField','당월마감액':'IntegerField','당월마감액_HI':'IntegerField','당월마감액_PO':'IntegerField',
                    '익월마감액':'IntegerField','익월마감액_HI':'IntegerField','익월마감액_PO':'IntegerField'}
        table_header = list(fields_model.keys())
        self.res_dict = {
			'fields_model' : fields_model,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {},
			'fields_delete' : {},
			'table_config' : {
				'table_header' : table_header,
				'no_Edit_cols' : [],
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'hidden_columns' :[],
				'cols_width' : {} ,
				'no_vContextMenuCols' : table_header ,### vContext menu를 생성하지 않는 col.
				'no_hContextMenuRows' :[],
				'v_Menus' : {
				},
				'h_Menus' : {
				},
				'cell_Menus':{
				}
			}

		}
        return self.res_dict
    
    def _get_data_from_request(self, request):
        try:
            기준년월 = request.data.get('기준년월', None)
            _마감일기준 = request.data.get('마감일기준', None)
            _UV_마감일기준 = request.data.get('UV_마감일기준', None)
            category = request.data.get('category', None)

            if  not all([기준년월, _마감일기준, _UV_마감일기준]):
                return Response({'error': '기준년월, 마감일기준, UV_마감일기준 모두 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
   
            마감일기준 = datetime.datetime.strptime(_마감일기준, '%Y-%m-%d').date()
            UV_마감일기준 = datetime.datetime.strptime(_UV_마감일기준, '%Y-%m-%d').date()
            return 기준년월, 마감일기준, UV_마감일기준, category
        except Exception as e:
            raise e

    def _get_query_values(self, query_values_list):
        """ 영업수주 요약 데이터 조회  """

        return (self.MODEL.objects
                        .select_related('관리_fk', '일정_fk', '의장_fk')
                        .exclude(Q(신우_실제금액__isnull=True) | Q(신우_실제금액=0))
                        .exclude( 일정_fk__isnull=True)
                        .filter(관리_fk__기준년월 = self.기준년월)  
                        .values(*query_values_list)
        )

    def post(self, request, *args, **kwargs):
        """ 영업수주 요약 데이터 조회 
            필수 data : 기준년월, 마감일기준, UV_마감일기준, category
            기준년월 : YYYY-MM
            마감일기준 : YYYY-MM-DD
            UV_마감일기준 : YYYY-MM-DD
            category : custom define으로, 의장, 호기번호, Proj_번호로 해서 merge 기준이 됨. 
        """
        print ( '영업수주_Summary_Api post : ', request.data )
        try:
            self.기준년월, self.마감일기준, self.UV_마감일기준, self.category = self._get_data_from_request(request)
   
            # QS = self.MODEL.objects.filter(관리_fk__id=수주관리_id).select_related('관리_fk', '일정_fk', '의장_fk')       
            query_values_list = [ 'Proj_번호', '호기번호', '신우_실제금액', '일정_fk__DOOR_출하요청일', '의장_fk__의장', '의장_fk__기준' ]
            queryset = self._get_query_values( query_values_list)
            
            _data = {'result':self._make_result_list( queryset), 'db_fields': self._init_res_dict() }
            
            return Response(_data, status=status.HTTP_200_OK)

        except Exception as e:
            print ( '영업수주_Summary_Api post 오류 발생:', e )
            return custom_response(e)

    def _make_result_list(self, queryset) -> list[dict]:
        """ 영업수주 요약 데이터 조회 
            필수 data : 기준년월, 마감일기준, UV_마감일기준, category
            기준년월 : YYYY-MM
            마감일기준 : YYYY-MM-DD
            UV_마감일기준 : YYYY-MM-DD
            category : custom define으로, 의장, 호기번호, Proj_번호로 해서 merge 기준이 됨. 
        """
        def get_keyName(item,category):
            Proj_번호, 호기번호 ,의장 = item['Proj_번호'], item['호기번호'], item['의장_fk__의장']
            match category:
                case '의장':
                    return f'{호기번호}_{의장}'
                case '호기번호':
                    return f'{호기번호}'
                case 'Proj_번호':
                    return f'{Proj_번호}'
        def get_그룹_dict(item,category):
            default_dict = {
                'Proj_번호': item['Proj_번호'],
                '호기번호': item['호기번호'],
                '신우_실제금액': 0,
                'DOOR_출하요청일': item['일정_fk__DOOR_출하요청일'],
                '의장_fk__의장': item['의장_fk__의장'],                            
                '당월마감액': 0,
                '당월마감액_HI': 0,
                '당월마감액_PO': 0,
                '익월마감액': 0,
                '익월마감액_HI': 0,
                '익월마감액_PO': 0,
            }
            match category:
                case '의장':
                    pass
                case '호기번호':
                    del default_dict['의장_fk__의장']
                case 'Proj_번호':
                    del default_dict['의장_fk__의장']
                    del default_dict['호기번호']
            return default_dict

                
        기준년월, 마감일기준, UV_마감일기준, category = self.기준년월, self.마감일기준, self.UV_마감일기준, self.category
        호기번호_list = list ( set ( queryset.values_list('호기번호', flat=True) ) )
        Proj_번호_list = list ( set ( queryset.values_list('Proj_번호', flat=True) ) )
        ### 그룹별 합계 저장
        grouped_sum = {}

        # category별 그룹화 및 금액 합산        
        count = 0
        category_group_dict :dict[str, dict] = {}
        for item in queryset:
            호기번호 = item['호기번호']
            DOOR_출하요청일 = item['일정_fk__DOOR_출하요청일']
            의장 = item['의장_fk__의장']
            keyName = get_keyName(item,category)
            ### category별 그룹 생성            
            if keyName not in category_group_dict:
                category_group_dict[keyName] = get_그룹_dict(item,category)

    
            # # 기준일 이전의 데이터만 처리
            # if count < 100:
            #     print ( 'DOOR_출하요청일 :', DOOR_출하요청일 , '기준일 :', 기준일 , DOOR_출하요청일 < 기준일 )
            #     count += 1
            실제금액 = item['신우_실제금액'] or 0
            HI_실제금액 = item['신우_실제금액']  if item['의장_fk__기준'] == 'HI' else 0
            PO_실제금액 = item['신우_실제금액']  if item['의장_fk__기준'] == 'PO' else 0

            _dict = category_group_dict[keyName]
            _dict['신우_실제금액'] += 실제금액
            if  DOOR_출하요청일 and DOOR_출하요청일 <= 마감일기준:
                _dict['당월마감액'] += 실제금액
                _dict['당월마감액_HI'] += HI_실제금액
                _dict['당월마감액_PO'] += PO_실제금액

            elif DOOR_출하요청일 and DOOR_출하요청일 > 마감일기준:
                if item['의장_fk__기준'] == 'HI':
                    _dict['익월마감액'] += 실제금액
                    _dict['익월마감액_HI'] += 실제금액
                elif item['의장_fk__기준'] == 'PO':
                    if DOOR_출하요청일 and DOOR_출하요청일 <= UV_마감일기준:
                        _dict['익월마감액_PO'] += 실제금액


        # 결과 리스트로 변환
        결과 = list(category_group_dict.values())
        return 결과
            




import traceback
def custom_response(e):
    error_traceback = traceback.format_exc()
    print ( 'simulation 오류 발생:', e )
    print ( 'simulation 오류 발생:', error_traceback )
    return Response({
        'error': str(e),
        'traceback': error_traceback
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class 영업수주_Simulation_Api(APIView):

    def post(self, request):
        try:
            print ( '시뮬레이션 시작:', request.data )
            수주_id = request.data.get('수주_id')
            if not 수주_id:
                return Response({'error': '수주_id가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 영업수주_관리 객체 가져오기    
            try:
                영업수주_관리_obj = 영업수주Models.영업수주_관리.objects.get(id=수주_id)   
            except 영업수주Models.영업수주_관리.DoesNotExist:
                return Response({'error': '해당 ID의 영업수주_관리가 존재하지 않습니다.'}, status=status.HTTP_404_NOT_FOUND)
            
            import random
            from django.db import transaction
            from django.db.models import F, Q
            
            # 트랜잭션 격리 수준 변경 및 각 작업을 별도 트랜잭션으로 분리
            
            # 1. 일정 simulation
            start_time = time.time()
            empty_일정_count = 0
            일정_ids:list[int] = list(영업수주Models.영업수주_일정.objects.filter(관리_fk=영업수주_관리_obj).values_list('id', flat=True))

            if not 일정_ids:
                return Response({'error': '해당 영업수주에 일정 데이터가 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 일정_fk가 null인 금액 데이터 조회
            empty_일정_fk_QS = 영업수주Models.영업수주_금액.objects.filter(
                관리_fk=영업수주_관리_obj,
                일정_fk__isnull=True
            ).values('id','호기번호')

            # 호기번호별로 id 목록을 그룹화 : {호기번호: [id1, id2, ...],...}
            호기번호_id_dict = {}
            for item in empty_일정_fk_QS:
                호기번호 = item['호기번호']
                if 호기번호 not in 호기번호_id_dict:
                    호기번호_id_dict[호기번호] = []
                호기번호_id_dict[호기번호].append(item['id'])
            
            # 업데이트할 데이터 수
            empty_일정_count = empty_일정_fk_QS.count()
            print(f"empty_일정_fk_QS : {empty_일정_count}")
            
            dict_총수 = len(호기번호_id_dict)
            with transaction.atomic():
                for cnt, (호기번호, id_list) in enumerate(호기번호_id_dict.items()):
                    random_일정_id = random.choice(일정_ids)
                    영업수주Models.영업수주_금액.objects.filter(id__in=id_list).update(일정_fk_id=random_일정_id)
                    if cnt % (dict_총수 // 5) == 0:  # 20%씩 진행 상황 출력
                        print(f"일정 할당 진행: {cnt}/{dict_총수} ({int(cnt/dict_총수*100)}%)")
            time.sleep(0.01)
            print ( '일정 할당 완료 :', time.time() - start_time )
            
            # 2. 금액 simulation
            start_time = time.time()
            empty_금액_count = 0
            empty_금액_ids = 영업수주Models.영업수주_금액.objects.filter(
                관리_fk=영업수주_관리_obj
            ).filter(
                Q(신우_실제금액=0) | Q(신우_실제금액__isnull=True)
            ).values_list('id', flat=True)
            print('empty_금액_count :', empty_금액_ids.count()  )

            dict_총수 = len(empty_금액_ids)
            batch_size = int(dict_총수 // 5)  # 20%씩 처리
            
            with transaction.atomic():
                for i in range(0, dict_총수, batch_size):
                    # 현재 배치의 ID 목록
                    batch_ids = empty_금액_ids[i:i+batch_size]
                    
                    # 일괄 업데이트 수행
                    ( 영업수주Models.영업수주_금액.objects
                        .filter(id__in=batch_ids)
                        .update(신우_실제금액=random.randrange(50000, 200001, 1000))
                    )
                    
                    # 진행 상황 출력
                    progress = min(i + batch_size, dict_총수)
                    print(f"금액 할당 진행: {progress}/{dict_총수} ({int(progress/dict_총수*100)}%)")
            time.sleep(0.01)
            print ( '금액 할당 완료 :', time.time() - start_time )
            
            # 3. 의장 simulation
            start_time = time.time()
            empty_의장_count = 0
            의장_ids = list(영업수주Models.자재내역_To_의장_Mapping.objects.all().values_list('id', flat=True))

            empty_의장_fk_ids = 영업수주Models.영업수주_금액.objects.filter(
                관리_fk=영업수주_관리_obj,
                의장_fk__isnull=True
            ).values_list('id', flat=True)
            print('empty_의장_count :', empty_의장_fk_ids.count()  )

            dict_총수 = len(empty_의장_fk_ids)
            batch_size = int(dict_총수 // 5)  # 20%씩 처리
            with transaction.atomic():
                for i in range(0, dict_총수, batch_size):
                    # 현재 배치의 ID 목록
                    batch_ids = empty_의장_fk_ids[i:i+batch_size]

                    ( 영업수주Models.영업수주_금액.objects
                        .filter(id__in=batch_ids)
                        .update(의장_fk_id=random.choice(의장_ids))
                    )
                    
                    # 진행 상황 출력
                    progress = min(i + batch_size, dict_총수)
                    print(f"의장 할당 진행: {progress}/{dict_총수} ({int(progress/dict_총수*100)}%)")

            time.sleep(0.01)
            print ( '의장 할당 완료 :', time.time() - start_time )



            return Response({
                'success': True,
                '일정_할당': {
                    'message': f'{empty_일정_count}개의 금액 데이터에 일정이 랜덤하게 할당되었습니다.',
                    '할당된_데이터_수': empty_일정_count
                },
                '금액_할당': {
                    'message': f'{empty_금액_count}개의 금액 데이터에 신우_실제금액이 랜덤하게 할당되었습니다.',
                    '할당된_데이터_수': empty_금액_count
                },
                '의장_할당': {
                    'message': f'{empty_의장_count}개의 금액 데이터에 의장이 랜덤하게 할당되었습니다.',
                    '할당된_데이터_수': empty_의장_count
                }
            }, status=status.HTTP_200_OK)
            
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print ( 'simulation 오류 발생:', e )
            print ( 'simulation 오류 발생:', error_traceback )
            return Response({
                'error': str(e),
                'traceback': error_traceback
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Process_영업수주_등록_Api(APIView):

    def post(self, request):   

        def _get_ws_msg(user_id, subject,message, progress:int=0):
            msg = {
                'main_type': 'notice',
                'sub_type': '영업수주_등록_진행',
                'receiver': [user_id],
                "subject": subject,
                'message': message,
                'sender' : 1,
                'progress': progress,
            }
            return msg
        
        try:
            # 요청에서 영업수주_관리 ID 가져오기
            수주_id = request.data.get('id')
            print('수주_id :', 수주_id, request.user.id)
            if not 수주_id:
                return Response({'error': '영업수주_관리 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 영업수주_관리 객체 가져오기    
            try:
                영업수주_관리_obj = 영업수주Models.영업수주_관리.objects.filter(
                    is_confirmed=False, 기준년월=request.data.get('기준년월')).get(id=수주_id)   
            except 영업수주Models.영업수주_관리.DoesNotExist:
                return Response({'error': '해당 ID의 영업수주_관리가 존재하지 않습니다.'}, status=status.HTTP_404_NOT_FOUND)

            # 사용자 정보 가져오기
            user_id = request.user.id

            # # 초기 알림 전송
            ws_sender = WebSocketMessageSender(영업수주_관리_obj, settings.WS_URL_영업수주진행현황, receiver=[user_id])
            # ws_sender.subject("영업수주 등록 처리를 시작합니다.") \
            #         .message("과정인 \n1. 일정 확정(db 저장 후 완료) \n2. 금액 확정(db 저장 후 완료) => 의장 및 일정을 가져옵니다. \n3. 영업수주 등록 완료(db 저장 후 완료) \n--- 완료 후 영업수주 관리 화면에서 확인 가능합니다. ---") \
            #         .progress(10) \
            #         .send()
            # time.sleep(1)

            # 1단계: 일정 확정 처리
            # ws_sender.subject("일정 확정 처리 중...") \
            #         .message("일정 확정 처리 중...") \
            #         .progress(10) \
            #         .send()
  
            # 일정 확정 처리
            try:
                일정_프로세서 = 영업수주_일정_프로세서(
                    영업수주_관리_obj, 
                    ws_sender = ws_sender,
                    MODEL = 영업수주Models.영업수주_일정
                )
                일정_result = 일정_프로세서.process()
                
                if '오류' in 일정_result:
                    raise Exception(일정_result['오류'])
                
            except Exception as e:
                # 일정 확정 실패 처리
                # ws_sender.subject("일정 확정 처리 실패") \
                #         .message(f"오류: {str(e)}") \
                #         .progress(0) \
                #         .send()
                raise
            
            # 2단계: 금액 확정 처리
            # ws_sender.subject("일정 확정 처리 완료 및 금액 처리 시작") \
            #         .message("일정 확정 처리 완료 및 금액 처리 시작") \
            #         .progress(30) \
            #         .send()
            
            # 금액 확정 처리
            try:
                금액_프로세서 = 영업수주_금액_프로세서(영업수주_관리_obj, ws_sender=ws_sender, MODEL=영업수주Models.영업수주_금액)
                금액_result = 금액_프로세서.process()
                
                if '오류' in 금액_result:
                    raise Exception(금액_result['오류'])
                
                # 최종 상태 업데이트
                # 영업수주_관리_obj.is_confirmed = True
                # 영업수주_관리_obj.save(update_fields=['is_confirmed'])
            except Exception as e:
                # 금액 확정 실패 처리
                # ws_sender.subject("금액 확정 처리 실패") \
                #         .message(f"오류: {str(e)}") \
                #         .progress(0) \
                #         .send()
 
                raise

            # 최종 완료 알림
            # ws_sender.subject("금액 확정 처리 완료") \
            #         .message("금액 확정 처리 완료") \
            #         .progress(100) \
            #         .send()  

            # 최종 결과 반환
            result = {
                'success': True,
                '일정_result': 일정_result,
                '금액_result': 금액_result
            }

 
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
                
            return Response({
                'error': str(e),
                'traceback': error_traceback
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class 영업수주_관리_ViewSet(viewsets.ModelViewSet):
    MODEL = 영업수주Models.영업수주_관리
    # TABLE_NAME = f"영업수주_관리_appID_{utils.get_tableName_from_api권한(div='영업수주', name='관리')}"
    queryset = MODEL.objects.all()
    serializer_class = 영업수주Serializers.영업수주_관리_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =[] 

    # utils.generate_table_config_db( 
    #     table_name=TABLE_NAME, 
    #     model_field = utils.get_MODEL_field_type(MODEL),
    #     serializer_field = utils.get_Serializer_field_type( 영업수주Serializers.영업수주_관리_Serializer() ),
    # )
    

    def get_queryset(self):
        queryset = self.MODEL.objects.select_related('등록자_fk').order_by('-id')
        return queryset
    
    def create(self, request, *args, **kwargs):
        print ( 'create 호출됨: ', request.data )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()  # 직접 save() 호출하여 인스턴스 얻기
        # self.perform_create(serializer)  # 정의가 serializer.save() method 실행하고, no return

        # 백그라운드 작업 큐에 추가
        queue = django_rq.get_queue('default')
        job = queue.enqueue(preprocess_excel_file, instance.id)


        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class 영업수주_일정_ViewSet(viewsets.ModelViewSet):
    MODEL = 영업수주Models.영업수주_일정
    queryset = MODEL.objects.all()
    serializer_class = 영업수주Serializers.영업수주_일정_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =[] 
    # filterset_class = 영업수주Models.영업수주_일정_FilterSet


    def get_queryset(self):
        queryset = self.MODEL.objects.all()
        # queryset = queryset.filter(상태='영업수주')
        return queryset
    
    @action(detail=False, methods=['POST'], url_path='excel-upload-bulk')
    def excel_upload_bulk(self, request):
        """
        Excel 파일을 업로드하여 영업수주_일정 데이터를 생성합니다.
        """
        try:
            print (' excel_upload_bulk 호출됨 ')

            #### 기존 db 삭제
            self.MODEL.objects.all().delete()
            #### 
            if 'file' not in request.FILES:
                return Response({'error': '파일이 제공되지 않았습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            excel_file = request.FILES['file']
            
            # 파일 확장자 확인
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                return Response({'error': 'Excel 파일만 업로드 가능합니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Excel 파일 읽기
            df = pd.read_excel(excel_file)
            _dictList = df.to_dict(orient='records')

            # 디버깅을 위한 데이터 출력
            # print("데이터 샘플:", _dictList[0] if _dictList else "데이터 없음")
            
            # # 필수 컬럼 확인 (필요한 컬럼 목록을 정의하세요)
            # required_columns = ['고객사', '프로젝트명', '납기일']  # 예시 컬럼, 실제 모델에 맞게 수정 필요
            # missing_columns = [col for col in required_columns if col not in df.columns]
            
            # if missing_columns:
            #     return Response(
            #         {'error': f'다음 필수 컬럼이 없습니다: {", ".join(missing_columns)}'},
            #         status=status.HTTP_400_BAD_REQUEST
            #     )
            
            # 데이터 처리 및 저장
            created_count = 0
            # 데이터 준비
            bulk_create_data = []
            # 날짜 형식 처리
            날짜fields = ['기계실_출하요청일', '구조물_출하요청일', '출입구_출하요청일', 'DOOR_출하요청일', 'CAGE_출하요청일', '바닥재_출하요청일',
                        '착공일', '설치투입일', '준공예정일', '준공일']
            with transaction.atomic():
                for idx, _dict in enumerate(_dictList):
                    try:
                        # NaN 값 처리
                        cleaned_dict = {}
                        for key, value in _dict.items():
                            if pd.isna(value):
                                cleaned_dict[key] = None
                            elif key in 날짜fields and value is not None:
                                # 날짜 형식 변환 시도
                                try:
                                    if isinstance(value, str):
                                        cleaned_dict[key] = parse_date(value)
                                    else:
                                        cleaned_dict[key] = value
                                except Exception as date_error:
                                    print(f"날짜 변환 오류 ({key}): {value}, 오류: {date_error}")
                                    cleaned_dict[key] = None
                            else:
                                cleaned_dict[key] = value
   
                        # 객체 생성 (아직 저장하지 않음)
                        영업수주_일정 = 영업수주Models.영업수주_일정(**cleaned_dict)
                        bulk_create_data.append(영업수주_일정)
                    except Exception as e:
                        print(f"행 {idx+1} 처리 중 오류 발생: {e}")
                        return Response({'error': f'행 {idx+1} 처리 중 오류: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
                
                # 한 번에 bulk create 수행
                if bulk_create_data:
                    try:
                        영업수주Models.영업수주_일정.objects.bulk_create(bulk_create_data)
                        created_count = len(bulk_create_data)
                    except Exception as bulk_error:
                        print(f"bulk_create 중 오류: {bulk_error}")
                        return Response({'error': f'데이터 저장 중 오류: {str(bulk_error)}'}, status=status.HTTP_400_BAD_REQUEST)
            
            result = {
                'success': True,
                'created_count': created_count,
            }
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"엑셀 업로드 중 오류 발생: {e}")
            print(f"상세 오류: {error_traceback}")
            return Response({
                'error': str(e),
                'traceback': error_traceback
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class 영업수주_금액_ViewSet(viewsets.ModelViewSet):
    MODEL = 영업수주Models.영업수주_금액    
    queryset = MODEL.objects.all()
    serializer_class = 영업수주Serializers.영업수주_금액_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =[] 
    # filterset_class = 영업수주Models.영업수주_일정_FilterSet


    def get_queryset(self):
        queryset = self.MODEL.objects.all()
        # queryset = queryset.filter(상태='영업수주')
        return queryset
    
    @action(detail=False, methods=['POST'], url_path='excel-upload-bulk')
    def excel_upload_bulk(self, request):
        """
        Excel 파일을 업로드하여 영업수주_일정 데이터를 생성합니다.
        """
        error_logs = []
        try:
            print (' excel_upload_bulk 호출됨 ')
            s = time.time()
            print ( 'reading excel file ...', datetime.datetime.now())
            #### 기존 db 삭제
            self.MODEL.objects.all().delete()
            #### 
            if 'file' not in request.FILES:
                return Response({'error': '파일이 제공되지 않았습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            excel_file = request.FILES['file']
            
            # 파일 확장자 확인
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                return Response({'error': 'Excel 파일만 업로드 가능합니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Excel 파일 읽기
            _usecols = ['발주번호','Proj_번호','공사_현장명','자재번호','자재내역','호기번호_WBS','단위','발주단가','발주수량','금액','발주잔량',
                        '신우_단가','신우_실제금액', '도면번호','현장대수','변경납기일','최초납기일', '생산계획일', '설치협력사','출하일자', '공사주석','거래명세서번호' ]
            # _dtype = {'발주번호':str, 'Proj_번호':str, '공사_현장명':str, '자재번호':str, '자재내역':str, '호기번호_WBS':str, '단위':str, 
            #           '발주단가':int, '발주수량':int, '금액':int, '발주잔량':int,
            #             '신우_단가':int, '신우_실제금액':int, '도면번호':str, '현장대수':int, 
            #             '변경납기일':str, '최초납기일':str, '생산계획일':str, '설치협력사':str, '출하일자':str, '공사주석':str, '거래명세서번호':str }
            # df = pd.read_excel(excel_file, usecols=_usecols, dtype=_dtype)

            _dtype = {'발주번호':str, 'Proj_번호':str, '공사_현장명':str, '자재번호':str, '자재내역':str, '호기번호_WBS':str, '단위':str, 
                    '도면번호':str, '현장대수':str, 
                    '변경납기일':str, '최초납기일':str, '생산계획일':str, '설치협력사':str, '출하일자':str, '공사주석':str, '거래명세서번호':str }
            df = pd.read_excel(excel_file, usecols=_usecols, dtype=_dtype)
            
            # 숫자 컬럼 처리 - 콤마 제거 및 정수 변환
            numeric_columns = ['발주단가', '발주수량', '금액', '발주잔량', '신우_단가', '신우_실제금액', '현장대수']
            for col in numeric_columns:
                if col in df.columns:
                    # 콤마 제거, 소수점 제거하고 정수로 변환
                    df[col] = df[col].apply(lambda x: 
                        int(float(str(x).replace(',', ''))) if pd.notna(x) and str(x).strip() != '' else None)
           
            _dictList = df.to_dict(orient='records')
            # 디버깅을 위한 데이터 출력
            print ('Reading exce to dict ...', datetime.datetime.now(), time.time() - s)
            # print("데이터 샘플:", _dictList[0] if _dictList else "데이터 없음")
            
            # # 필수 컬럼 확인 (필요한 컬럼 목록을 정의하세요)
            # required_columns = ['고객사', '프로젝트명', '납기일']  # 예시 컬럼, 실제 모델에 맞게 수정 필요
            # missing_columns = [col for col in required_columns if col not in df.columns]
            
            # if missing_columns:
            #     return Response(
            #         {'error': f'다음 필수 컬럼이 없습니다: {", ".join(missing_columns)}'},
            #         status=status.HTTP_400_BAD_REQUEST
            #     )
            
            # 데이터 처리 및 저장
            created_count = 0
            # 데이터 준비
            bulk_create_data = []
            # 날짜 형식 처리
            날짜fields = ['납품예정일', '최초입력일자', '변경일자','입고예정일','변경납기일','최초납기일','생산계획일','생산계획변경일',
                    'JAMB_실측일','출하일자'                ]
            날짜fields_datetime = ['납기일변경일시','특성치변경일시','발주승인일시','발주삭제일시']

            with transaction.atomic():
                QS_자재내역_To_의장_Mapping = 영업수주Models.자재내역_To_의장_Mapping.objects.all()
                print ( 'QS_자재내역_To_의장_Mapping', QS_자재내역_To_의장_Mapping )
                s = time.time()
                print(f"bulk create dict 시작  :{datetime.datetime.now()}, bulk_create_data 개수: {len(_dictList)}")
                QS_일정 = 영업수주Models.영업수주_일정.objects.all()
                prev호기 = None
                prevInstance일정 = None
                targetList = _dictList[:5000]
                for idx, _dict in enumerate(targetList):
                    if idx % 1000 == 0:
                        print(f"bulk create dict 진행중  :{time.time() - s}, idx: {idx}, 남은 개수: {len(targetList) - idx}")
                    try:
                        # NaN 값 처리
                        cleaned_dict = {}
                        for key, value in _dict.items():
                            if pd.isna(value):
                                cleaned_dict[key] = None
                            elif key in 날짜fields and value is not None:
                                # 날짜 형식 변환 시도
                                try:
                                    if isinstance(value, str):
                                        cleaned_dict[key] = parse_date(value)
                                    else:
                                        cleaned_dict[key] = value
                                except Exception as date_error:
                                    print(f"날짜 변환 오류 ({key}): {value}, 오류: {date_error}")
                                    cleaned_dict[key] = None
                            elif key in 날짜fields_datetime and value is not None:
                                # Datetime 변환 시도
                                try:
                                    if isinstance(value, str):
                                        cleaned_dict[key] = parse_datetime(value)
                                    else:
                                        cleaned_dict[key] = value
                                except Exception as date_error:
                                    print(f"Datetime 변환 오류 ({key}): {value}, 오류: {date_error}")
                                    cleaned_dict[key] = None
                            else:
                                                                # 문자열 필드의 길이 제한 처리 추가
                                if isinstance(value, str) and len(value) > 250:
                                    if key == '공사주석':   ### textfield 라서 모두 저장
                                        pass
                                    else:
                                        # 문자열이 너무 길면 자르고 로그에 기록
                                        original_value = value
                                        value = value[:250]
                                        error_message = f"행 {idx+1}: 필드 '{key}'의 값이 너무 깁니다. 원본 길이: {len(original_value)}자, 250자로 잘랐습니다."
                                        error_logs.append(error_message)
                                        print(error_message)
                                cleaned_dict[key] = value

                        #### 일정_fk
                        cleaned_dict['호기번호'] = cleaned_dict['호기번호_WBS'].split('-')[0]
                        if prev호기 != cleaned_dict['호기번호']:
                            prev호기 = cleaned_dict['호기번호']
                            currentInstance일정 = QS_일정.filter(호기번호=cleaned_dict['호기번호']).first()
                            prevInstance일정 = currentInstance일정
                        # _일정_instance = 영업수주Models.영업수주_일정.objects.get(호기번호=cleaned_dict['호기번호'])                            
                        else:
                            currentInstance일정 = prevInstance일정

                        cleaned_dict['일정_fk'] = currentInstance일정
                        if not currentInstance일정:
                            error_message = f"행 {idx+1}: 호기번호 {cleaned_dict['호기번호']}에 해당하는 일정이 없습니다."
                            error_logs.append(error_message)
                            
                        # cleaned_dict['일정_fk'] = 영업수주Models.영업수주_일정.objects.get(호기번호=cleaned_dict['호기번호'])
                        
                        # 모든 의장 객체를 가져와서 포함 관계 확인
                        for 의장_obj in QS_자재내역_To_의장_Mapping:
                            if 의장_obj.자재내역 in cleaned_dict['자재내역']:  # 의장 값이 cleaned_dict['의장']에 포함되는지 확인
                                cleaned_dict['의장_fk'] = 의장_obj
                                break
                        # 객체 생성 (아직 저장하지 않음)
                        영업수주_금액 = self.MODEL(**cleaned_dict)
                        bulk_create_data.append(영업수주_금액)
                    except Exception as e:
                        print(f"행 {idx+1} 처리 중 오류 발생: {e}")
                        return Response({'error': f'행 {idx+1} 처리 중 오류: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
                
                print ('bulk create dict 완료 ...', datetime.datetime.now(), time.time() - s)
                # 한 번에 bulk create 수행

                s = time.time()
                print(f"bulk create 시작  :{datetime.datetime.now()}, bulk_create_data 개수: {len(bulk_create_data)}")
                if bulk_create_data:
                    try:
                        self.MODEL.objects.bulk_create(bulk_create_data, batch_size= _get_batch_size(bulk_create_data))
                        created_count = len(bulk_create_data)
                        print(f"bulk create 완료  :{datetime.datetime.now()}, created_count: {created_count}, 소요시간: {time.time() - s}")
                    except Exception as bulk_error:
                        print(f"bulk_create 중 오류: {bulk_error}")
                        return Response({'error': f'데이터 저장 중 오류: {str(bulk_error)}'}, status=status.HTTP_400_BAD_REQUEST)

            result = {
                'success': True,
                'created_count': created_count,
                'error_logs': error_logs,
            }
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"엑셀 업로드 중 오류 발생: {e}")
            print(f"상세 오류: {error_traceback}")
            return Response({
                'error': str(e),
                'traceback': error_traceback
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['GET'], url_path='자재내역_To_의장_Mapping')
    def 자재내역_To_의장_Mapping(self, request):
        """
        자재내역을 의장으로 매핑합니다.
        """

        return Response(
            data=영업수주Signal.process_자재내역_To_의장_Mapping(), 
            status=status.HTTP_200_OK)
        




class 자재내역_To_의장_Mapping_ViewSet(viewsets.ModelViewSet):
    MODEL = 영업수주Models.자재내역_To_의장_Mapping    
    queryset = MODEL.objects.all()
    serializer_class = 영업수주Serializers.자재내역_To_의장_Mapping_Serializer  
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =[] 
    # filterset_class = 영업수주Models.영업수주_일정_FilterSet

    def get_queryset(self):
        queryset = self.MODEL.objects.all()
        return queryset
        
