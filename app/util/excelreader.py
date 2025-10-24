import pandas as pd
import pickle, hashlib, os
import logging
from django.core.cache import cache


class ExcelReader:
    """
    엑셀 파일 읽기를 위한 유틸리티 클래스
    
    사용 예시:
    ```
    # 기본 사용법
    reader = ExcelReader(file_path)
    df = reader.read()
    
    # 캐싱 사용
    reader = ExcelReader(file_path, use_cache=True, cache_key_prefix="my_prefix")
    df = reader.read()
    
    # 특정 컬럼과 데이터 타입 지정
    reader = ExcelReader(file_path, usecols=['A', 'B'], dtype={'A': str})
    df = reader.read()
    ```
    """
    
    def __init__(self, file_path, usecols:list[str]=None, dtype:dict[str,type]=None, use_cache:bool=False, cache_key_prefix:str=None, cache_ttl:int=3600):
        """
        엑셀 파일 읽기 유틸리티 초기화
        
        Args:
            file_path: 엑셀 파일 경로 (문자열 또는 파일 객체)
            usecols: 읽을 컬럼 목록 (선택적)
            dtype: 컬럼별 데이터 타입 (선택적)
            use_cache: 캐시 사용 여부 (기본값: False)
            cache_key_prefix: 캐시 키 접두사 (선택적)
            cache_ttl: 캐시 유효 시간(초) (기본값: 3600)
        """
        self.file_path = file_path
        self.usecols = usecols
        self.dtype = dtype
        self.use_cache = use_cache
        self.cache_key_prefix = cache_key_prefix or "excel_cache"
        self.cache_ttl = cache_ttl
        self.logger = logging.getLogger(__name__)
    
    def _get_cache_key(self):
        """캐시 키 생성"""
        if isinstance(self.file_path, str):
            file_mtime = os.path.getmtime(self.file_path)
            key_string = f'{self.file_path}_{file_mtime}'
        else:
            # 파일 객체인 경우 이름과 크기 사용
            key_string = f'{self.file_path.name}_{self.file_path.size}'
        
        # usecols와 dtype도 캐시 키에 포함
        if self.usecols:
            key_string += f'_cols:{",".join(map(str, self.usecols))}'
        if self.dtype:
            key_string += f'_dtype:{hash(str(self.dtype))}'
            
        return f"{self.cache_key_prefix}_{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def read(self, **kwargs):
        """
        엑셀 파일 읽기
        
        Args:
            **kwargs: pandas.read_excel에 전달할 추가 인수
            
        Returns:
            pandas.DataFrame: 읽은 데이터프레임
        """
        if self.use_cache:
            cache_key = self._get_cache_key()
            cached_data = cache.get(cache_key)
            
            if cached_data:
                self.logger.info(f"캐시에서 데이터 로드: {cache_key}")
                return pickle.loads(cached_data)
            
            self.logger.info(f"캐시 미스: {cache_key}")
        
        # 파일 확장자에 따라 엔진 선택
        if isinstance(self.file_path, str):
            engine = 'xlrd' if self.file_path.endswith('.xls') else 'openpyxl'
        else:
            engine = 'xlrd' if self.file_path.name.endswith('.xls') else 'openpyxl'
        
        # 기본 옵션 설정
        read_options = {
            'engine': engine,
            'na_filter': False,
            'keep_default_na': False
        }
        
        # usecols와 dtype 추가
        if self.usecols:
            read_options['usecols'] = self.usecols
        if self.dtype:
            read_options['dtype'] = self.dtype
        
        # 추가 옵션 적용
        read_options.update(kwargs)
        
        try:
            df = pd.read_excel(self.file_path, **read_options)
            
            if self.use_cache:
                # 데이터프레임을 피클로 직렬화하여 캐시에 저장
                pickled_df = pickle.dumps(df)
                cache_key = self._get_cache_key()
                cache.set(cache_key, pickled_df, self.cache_ttl)
                self.logger.info(f"데이터 캐싱 완료: {cache_key}")
            
            return df
        except Exception as e:
            self.logger.error(f"Excel 파일 읽기 오류: {str(e)}")
            raise Exception(f"Excel 파일 읽기 오류: {str(e)}")
    
    @classmethod
    def process_numeric_columns(cls, df, columns, fill_na=0, as_int=True):
        """
        숫자 컬럼 처리 (콤마 제거 및 숫자 변환)
        
        Args:
            df: 처리할 데이터프레임
            columns: 처리할 컬럼 목록
            fill_na: NA 값을 채울 값 (기본값: 0)
            as_int: 정수형으로 변환할지 여부 (기본값: True)
            
        Returns:
            pandas.DataFrame: 처리된 데이터프레임
        """
        df_copy = df.copy()
        for col in columns:
            if col in df_copy.columns:
                df_copy[col] = pd.to_numeric(
                    df_copy[col].astype(str).str.replace(',', ''), 
                    errors='coerce'
                ).fillna(fill_na)
                
                if as_int:
                    df_copy[col] = df_copy[col].astype(int)
        
        return df_copy
    
    @classmethod
    def process_date_columns(cls, df, date_columns, datetime_columns=None):
        """
        날짜 컬럼 처리
        
        Args:
            df: 처리할 데이터프레임
            date_columns: 날짜(date) 컬럼 목록
            datetime_columns: 날짜시간(datetime) 컬럼 목록
            
        Returns:
            pandas.DataFrame: 처리된 데이터프레임
        """
        df_copy = df.copy()
        
        # 날짜 컬럼 처리
        if date_columns:
            for col in date_columns:
                if col in df_copy.columns:
                    df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
                    # NaT 값을 None으로 변환
                    df_copy[col] = df_copy[col].where(~pd.isna(df_copy[col]), None)
        
        # 날짜시간 컬럼 처리
        if datetime_columns:
            for col in datetime_columns:
                if col in df_copy.columns:
                    df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
                    df_copy[col] = df_copy[col].where(~pd.isna(df_copy[col]), None)
        
        return df_copy
