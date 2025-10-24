# 웹소켓 메시지 전송 - 작업 시작
from util.websocketmessagesender import WebSocketMessageSender
from django.conf import settings
from django.core.cache import cache
import os, hashlib, pickle
import pandas as pd
from . import models as 영업수주Models
from util.excelreader import ExcelReader


def preprocess_excel_file(관리instance_id:int):
    """백그라운드에서 엑셀 파일 전처리"""
    try:
         # 관리 객체 가져오기
        관리_obj = 영업수주Models.영업수주_관리.objects.get(id=관리instance_id)
        
        # 금액 파일 처리
        if 관리_obj.금액file:
            # 캐시 키 생성 (파일 경로와 수정 시간 기반)
            file_path = 관리_obj.금액file.path
            file_mtime = os.path.getmtime(file_path)
            cache_key = f"excel_cache_{관리instance_id}_금액_{hashlib.md5(f'{file_path}_{file_mtime}'.encode()).hexdigest()}"
            
            # 엑셀 파일 읽기
            usecols = ['발주번호', 'Proj_번호', '공사_현장명', '자재번호', '자재내역', '호기번호_WBS', '단위',
                      '발주단가', '발주수량', '금액', '발주잔량', '신우_단가', '신우_실제금액', '도면번호',
                      '현장대수', '변경납기일', '최초납기일', '생산계획일', '설치협력사', '출하일자', '공사주석', '거래명세서번호']
            numeric_columns = ['발주단가', '발주수량', '금액', '발주잔량', '신우_단가', '신우_실제금액', '현장대수']
            dtype = {'발주번호': str, 'Proj_번호': str, '공사_현장명': str, '자재번호': str, '자재내역': str,
                    '호기번호_WBS': str, '단위': str, '발주번호': str, 
                    '도면번호': str, '현장대수': str, '변경납기일': str,
                    '최초납기일': str, '생산계획일': str, '설치협력사': str, '출하일자': str, '공사주석': str,
                    '거래명세서번호': str}
            

            # ExcelReader 클래스 사용
            reader = ExcelReader(
                file_path, 
                usecols=usecols, 
                dtype=dtype,
                use_cache=False
            )
            df = reader.read()

           
            # 숫자 컬럼 처리
            numeric_columns = ['발주단가', '발주수량', '금액', '발주잔량', '신우_단가', '신우_실제금액', '현장대수']
            df = ExcelReader.process_numeric_columns(df, numeric_columns)
            # 데이터프레임을 피클로 직렬화
            pickled_df = pickle.dumps(df)
            
            # 캐시에 저장 (TTL: 1시간)
            cache.set(cache_key, pickled_df, 3600)

            # 완료 메시지 전송
            ws_sender.subject("엑셀 파일 전처리 완료") \
                    .message("엑셀 파일 전처리가 완료되었습니다. 이제 영업수주 등록을 진행할 수 있습니다.") \
                    .progress(100) \
                    .send()
            
            print(f"금액 파일 전처리 완료: {cache_key}")
        
        # 일정 파일 처리 (유사한 방식으로)
        if 관리_obj.일정file:
            # 유사한 처리 로직...
            pass
            
    except Exception as e:
        print(f"파일 전처리 오류: {str(e)}")