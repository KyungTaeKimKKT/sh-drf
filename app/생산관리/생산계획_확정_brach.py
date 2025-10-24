from django.conf import settings
from django.db import models
from django.db.models import Q

from django.utils import timezone
from users.models import User # custom User model import
from datetime import datetime, date, timedelta

from 일일보고.models import 휴일_DB


class 확정_branch:
    작업_구분자 = ['+', '→']
    PO_작업명 = ['분체', 'UHC', '하드코팅']
    제품분류_DICT = {
        'Cage' : ['wall', '상판', ],
        'Door' : ['door','hatch', 'h/d'],
        'JAMB' : ['jamb']
    }

    def __init__(self):
        self.대구분 = ''
        

    def 확정_branch_run(self, saveModel, ddayModel, 대구분:str='htm'):
        self.대구분 = 대구분
        self.휴일_list = self._get_휴일_List()
        self.instance_Dday = ddayModel.objects.order_by('-id')[0]

        for db_obj in self._get_생산지시_process():
            # for key, value in db_obj.items():
            #     pass
            #     print (key , " : ", value)
            # print ( self.생산지시_fk.job_name, '\n\n')
            p = saveModel(**db_obj)
            p.save()

    def _get_휴일_List(self) ->list[date]:
        max_Date = Q(휴일__lte=max(self.납기일_Door, self.납기일_Cage) )
        min_Date = Q(휴일__gte= date.today() - timedelta(days=30) )
        qs_휴일 = 휴일_DB.objects.filter( max_Date & min_Date ).order_by('휴일')
        return list( qs_휴일.values_list('휴일', flat=True) )

    def _get_생산지시_process(self) -> list:
        생지_instance = self.생산지시_fk
        results =[]
        # 😀 all() 안하면, ==> TypeError: 'ManyRelatedManager' object is not iterable
        for process in 생지_instance.process_fks.all():            
            if not self._is_process_in_대구분(process) : continue
         
            작업list = self._get_작업_divide(process.상세Process)
            for 작업 in 작업list:
                db_obj = {}   
                db_obj['생산계획관리_fk'] = self
                db_obj['제품분류'] = self._get_제품분류(process)
                db_obj['최종납기일'] = getattr(self, f"납기일_{db_obj['제품분류']}", None)
                db_obj['생산지시_process_fk'] = process
                공정 = self._get_공정(작업)
                db_obj['공정'] = 공정
                db_obj['공정_완료계획일'] = self._get_공정별_완료계획일(db_obj['제품분류'],공정)
                db_obj['작업명'] = 작업
                db_obj['계획수량'] = self._get_계획수량(process, 공정, db_obj['제품분류'])
                db_obj['is_Active'] = True
                results.append(db_obj)

        return results
    
    def _is_process_in_대구분(self, process) -> bool:
        match self.대구분:
            case 'is_계획반영_htm':
                if self._get_제품분류(process) in ['Cage','Door']:
                    return True
            case 'is_계획반영_jamb':
                if self._get_제품분류(process) in ['JAMB']:
                    return True
        return False

    def _get_제품분류(self, process) -> str:
        """ Cage, Door, JAMB로 구분"""
        return self._get_str_contains_DictElements( process.적용, self.제품분류_DICT )


    def _get_공정 (self, 작업명:str) -> str:
        for po_작업명 in self.PO_작업명:
            if po_작업명 in 작업명:
                return 'PO'        
        return 'HI'

    def _get_공정별_완료계획일(self, 제품분류:str, 공정:str ) -> date|None:
        """ 제품분류에 따른 공정 완료일을 return"""
        납기일 = getattr(self, f"납기일_{제품분류}", None)
        if not 납기일 : return None

        dday = getattr(self.instance_Dday, f"_{공정}", None)
        if not dday : return None

        dday_date = self._get_not_in_휴일db(납기일)
        rest_day = abs(dday)
        while rest_day > 0:
            dday_date = self._get_not_in_휴일db(dday_date - timedelta(days=1))
            rest_day -= 1
        # print (납기일, dday_date, dday)
        return dday_date

    def _get_not_in_휴일db(self, targetDate) -> date:
        while self._is_in_휴일db(targetDate) :
            targetDate = targetDate - timedelta(days=1)
        return targetDate

    def _is_in_휴일db(self, targetDate) -> bool:
        # print ( targetDate, type(targetDate), bool(targetDate in self.휴일_list ) )
        return bool(targetDate in self.휴일_list )


    def _get_계획수량(self, process, 공정, 제품분류):
        match 공정:
            case 'HI':
                return process.수량
            case 'PO':
                match 제품분류:
                    case 'Cage' :
                        return process.수량 * ( str(process.비고).count(',') +1 )
                    case 'JAMB':
                        if '기준층' in process.적용 :
                            return self._get_Door_Count('기준층')
                        elif '기타층' in process.적용:
                            return self._get_Door_Count('기타층')
                    case 'Door' :
                        return process.수량
                    case _:
                        return process.수량                

        return process.수량

    def _get_작업_divide(self, 상세Process:str) -> list:
        상세_list = []
        if ( 구분자 := self._get_작업_구분자( 상세Process) ):
            상세_list = 상세Process.split(구분자)
            return [ self._clean_작업_str(작업) for 작업 in 상세_list]

        else:
            if '해당사항' in 상세Process:
                return 상세_list
            else:
                return [ 상세Process ]
        
        return  상세_list

    def _get_작업_구분자(self, 상세Process:str) -> str|None:
        for 구분자 in self.작업_구분자:
            if 구분자 in 상세Process:
                return 구분자
        return None
    
    def _clean_작업_str(self, 작업_str:str) -> str:
        """ text 중, \n, rstip() 하여 str return """
        return 작업_str.rstrip().replace('\n', '')
    
    def _get_str_contains_DictElements( self, string:str, checkDict:dict) -> str:
        """ string이 checkDict의 value(list)의 element를 포함하면 그 해당 key를 return"""
        for key, value in checkDict.items():
            for name in value:
                if name in string.lower():
                    return key

        return '미정'
    
    def _get_Door_Count(self, d_type:str='기준층') -> int:
        for process in self.생산지시_fk.process_fks.all():
            if 'hatch' in process.적용.lower() and  d_type in process.적용.lower():
                return process.수량
            
