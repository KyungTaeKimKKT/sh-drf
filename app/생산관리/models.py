from django.conf import settings
from django.db import models, transaction
from simple_history.models import HistoricalRecords

from django.utils import timezone
from users.models import User # custom User model import
from datetime import datetime, date, timedelta

import uuid
import 생산지시.models as 생지
from 일일보고.models import 휴일_DB


# from .생산계획_확정_brach import 확정_branch

class 판금처_DB(models.Model):
	판금처 = models.CharField(max_length=100)
	판금처_코드 = models.CharField(max_length=100)


class 생산계획_DDay(models.Model):
	_출하일 = models.IntegerField()
	_PO    = models.IntegerField()
	_판금  = models.IntegerField()
	_HI    = models.IntegerField()
	_구매  = models.IntegerField()
	_생지  = models.IntegerField()
	_작지  = models.IntegerField()

class ProductionLine(models.Model):
	구분 = models.CharField ( max_length= 10)		### HI,PO, PG등
	설비 = models.CharField ( max_length= 20 , default='')
	name = models.CharField( max_length=100)			#### LINE NAME
	capacity = models.IntegerField()  # 생산라인 용량
	is_active = models.BooleanField(default=True)
	
	# class Meta:
	# 	verbose_name = '생산라인'
	# 	verbose_name_plural = '생산라인들'


class 생산계획_확정Branch(models.Model):
	""" 생산계획관리에서  확정되면 save 될때 DB DATA생성함"""
	일정관리_fk = models.ForeignKey('생산계획_일정관리', on_delete=models.CASCADE, null=True, blank=True, related_name='일정관리_확정Branch_set')
	schedule_fk =  models.ForeignKey('Schedule_By_Types', on_delete=models.CASCADE, null=True, blank=True, related_name='schedule_확정Branch_set')        
	생산지시_process_fk = models.ForeignKey(생지.Process, on_delete=models.CASCADE, null=True, blank=True , related_name='process_확정Branch_set')   

	# production_line = models.ForeignKey ( ProductionLine, on_delete=models.SET_NULL, null=True,  related_name='line_확정Branch_set')
   
	공정_완료계획일 = models.DateField(  blank=True, null=True)
	작업명 = models.CharField(max_length=100,  null=True, blank=True) 
	계획수량 = models.IntegerField(null=True, blank=True)

	계획등록_timestamp = models.DateTimeField(default=timezone.now())
	is_Active = models.BooleanField( blank=True, null=True )

		### django-simple-history
	history = HistoricalRecords()

	def get_공정_details(self):
		"""해당 확정Branch에 연결된 모든 공정 상세 정보를 가져오는 메서드"""
		return self.공정상세_set.filter(is_active=True).order_by('공정순서')

class Schedule_By_Types(models.Model):
	출하_type = models.CharField(max_length=20)
	출하일 = models.DateField(null=True, blank=True)
	dday = models.ForeignKey('생산계획_DDay', on_delete=models.PROTECT)

	# process_fks = models.ManyToManyField(생산계획_확정Branch, related_name='_process_fks' )

	PO일정   = models.DateField(null=True) 
	판금일정   = models.DateField(null=True) 
	HI일정   = models.DateField(null=True) 
	구매일정   = models.DateField(null=True) 
	생지일정   = models.DateField(null=True) 
	작지일정   = models.DateField(null=True) 
	history = HistoricalRecords()

	def save(self, *args, **kwargs):
		if not self.pk:  # 새로운 인스턴스인 경우
			if self.출하일:
				self.일정계산()				
		else:  # 기존 인스턴스 수정의 경우
			이전_데이터 = Schedule_By_Types.objects.get(pk=self.pk)
			if self.출하일 != 이전_데이터.출하일:  # 출하일이 변경된 경우
				self.일정계산()
		super().save(*args, **kwargs)

		# if self.출하일 and :  # 새로운 인스턴스 생성 시에만
		# 	self.납기일_Door = min( [ hogi.납기일_Door for hogi in self.생산지시_fk.도면정보_fks.all() if hogi and hasattr( hogi, '납기일_Door' ) ] )
		# 	self.납기일_Cage = min( [ hogi.납기일_Cage for hogi in self.생산지시_fk.도면정보_fks.all() if hogi and hasattr( hogi, '납기일_Cage' ) ] )
		# super().save(*args, **kwargs)

	def 일정계산(self):
		휴일목록 = set(휴일_DB.objects.values_list('휴일', flat=True))
		
		# dday 설정값 매핑
		일정_매핑 = {
			'PO일정': self.dday._PO,
			'판금일정': self.dday._판금,
			'HI일정': self.dday._HI,
			'구매일정': self.dday._구매,
			'생지일정': self.dday._생지,
			'작지일정': self.dday._작지
		}

		# 각 공정별 일정 계산
		for 필드명, 일수 in 일정_매핑.items():
			계산된_일자 = self._계산_공정일(self.출하일, 일수, 휴일목록)
			setattr(self, 필드명, 계산된_일자)

	def _계산_공정일(self, 기준일, 이동일수, 휴일목록):
		target_date = 기준일
		remaining_days = abs(이동일수)
		
		while remaining_days > 0:
			target_date += timedelta(days=-1)
			if target_date not in 휴일목록:
				remaining_days -= 1
				
		return target_date

class 생산계획_일정관리(models.Model):
	생산지시_fk = models.ForeignKey(생지.생산지시, on_delete=models.CASCADE, null=True)
	schedule_cage_fk = models.ForeignKey(Schedule_By_Types, on_delete=models.CASCADE, null=True, related_name='_schedule_cage' )
	schedule_door_fk = models.ForeignKey(Schedule_By_Types, on_delete=models.CASCADE, null=True, related_name='_schedule_door' )
	schedule_jamb_fk = models.ForeignKey(Schedule_By_Types, on_delete=models.CASCADE, null=True, related_name='_schedule_jamb' )

	# schedule_fks = models.ManyToManyField(Schedule_By_Types , related_name='_schedule_fks')
	history = HistoricalRecords()

	def save(self, *args, **kwargs):
		is_new = not self.pk  # 새 인스턴스 여부 확인		

		if is_new:  # 새 인스턴스인 경우에만 실행
			dday = 생산계획_DDay.objects.last()
			
			for 출하타입 in ['Door', 'Cage', 'JAMB']:
				_obj = Schedule_By_Types.objects.create(
					출하_type=출하타입,
					dday=dday,
					출하일 = self._get_출하일(출하타입=출하타입)
				)
				setattr( self, f"schedule_{출하타입.lower()}_fk", _obj)
		super().save(*args, **kwargs)  # 첫 번째 저장
		# 마지막의 super().save() 제거

	def _get_출하일(self, 출하타입:str) :
		match  출하타입:
			case 'Door' | 'Cage':
				return  min( [ getattr( hogi, f'납기일_{출하타입}' ) for hogi in self.생산지시_fk.도면정보_fks.all() if hogi and hasattr( hogi, f'납기일_{출하타입}' ) ] )

			case 'JAMB':
				return None


class 생산계획_공정상세(models.Model):
	"""개별 공정의 상세 정보를 관리하는 모델"""
	확정Branch_fk = models.ForeignKey('생산계획_확정Branch', on_delete=models.CASCADE, related_name='공정상세_set')
	공정순서 = models.IntegerField(default=0)  # 전체 공정 중 순서
	공정명 = models.CharField(max_length=100)
	ProductionLine_fk = models.ForeignKey('ProductionLine', on_delete=models.SET_NULL, null=True)
	계획일 = models.DateField()
	생성일시 = models.DateTimeField(auto_now_add=True)
	수정일시 = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)
	is_HI_complete = models.BooleanField(default=False)

	class Meta:
		ordering = ['확정Branch_fk', '공정순서']
		indexes = [
            models.Index(fields=['확정Branch_fk', '공정순서']),
            models.Index(fields=['is_active']),
            models.Index(fields=['계획일']),
            models.Index(fields=['ProductionLine_fk'])
        ]

	def save(self, *args, **kwargs):
		is_new = not self.pk  # 새 인스턴스인지 확인
		super().save(*args, **kwargs)

		if is_new and self.is_active:  # 새로운 active 공정상세가 생성될 때만
			생산실적.objects.get_or_create(
				공정상세_fk=self,
				defaults={
					'실적수량': 0,
					'시작시간': None,
					'종료시간': None
				}
			)

class 생산실적(models.Model):
	"""각 공정별 실적 관리"""
	공정상세_fk = models.ForeignKey('생산계획_공정상세', on_delete=models.CASCADE, related_name='실적_set')
	실적수량 = models.IntegerField(default=0)
	시작시간 = models.DateTimeField(null=True, blank=True)
	종료시간 = models.DateTimeField(null=True, blank=True)
	작업자 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
	비고 = models.TextField(null=True, blank=True)
	등록일시 = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		ordering = ['공정상세_fk', '시작시간']

class 계획변경이력(models.Model):
	"""계획 변경 이력 관리"""
	공정상세_fk = models.ForeignKey('생산계획_공정상세', on_delete=models.CASCADE, related_name='변경이력_set')
	변경항목 = models.CharField(max_length=20)  # equipment, 계획일 등
	이전값 = models.CharField(max_length=100)
	변경값 = models.CharField(max_length=100)
	변경사유 = models.TextField(null=True, blank=True)
	변경자 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
	변경일시 = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-변경일시']


class 생산관리_제품완료(models.Model):
	확정Branch_fk = models.ForeignKey('생산계획_확정Branch', on_delete=models.CASCADE, related_name='제품완료_set')

	고객사 = models.CharField(max_length=15)
	구분 = models.CharField(max_length=10)
	Job_Name = models.CharField(max_length=100)
	Proj_No = models.CharField(max_length=100)
	계획수량 = models.IntegerField(default=0)
	실적수량 = models.IntegerField(default=0)
	소재 = models.CharField(max_length=20)
	치수 = models.CharField(max_length=20)
	공정명 = models.CharField(max_length=100)
	공정구분 = models.CharField ( max_length= 10)		### HI,PO, PG등
	설비명 = models.CharField( max_length=100)			#### LINE NAME
	계획일 = models.DateField(null=True, blank=True)
	완료일시 = models.DateTimeField(auto_now_add=True)
	완료자 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
	비고 = models.TextField(null=True, blank=True)

	@transaction.atomic
	def complete_processes(self, 공정상세_ids:list[int], 창고_fk:int):
		"""관련된 공정상세들의 완료 처리"""
		생산계획_공정상세.objects.filter(
			id__in=공정상세_ids,
			확정Branch_fk=self.확정Branch_fk
		).update(is_HI_complete=True)

       # Stock 생성 및 입고대기 처리
		self.create_stock(창고_fk)

	def create_stock(self, 창고_fk):
		"""입고대기 상태의 재고 생성"""
		from 재고관리.models import Stock, StockHistory  # 순환 참조 방지를 위해 지역 import
		
		# Stock 생성
		stock = Stock()
		stock.입고대기_생성(self, 창고_fk)
		
		# StockHistory 생성
		history = StockHistory()
		history.입고대기_생성(stock)
		
		return stock

# # 공정 상세 생성
# def create_process_details(확정branch, 상세process_list):
#     for idx, process in enumerate(상세process_list, 1):
#         생산계획_공정상세.objects.create(
#             확정Branch_fk=확정branch,
#             공정순서=idx,
#             공정명=process,
#             계획일=확정branch.공정_완료계획일
#         )

# # 계획 변경 시
# def update_process_plan(공정상세_id, equipment=None, 계획일=None):
#     공정 = 생산계획_공정상세.objects.get(id=공정상세_id)
	
#     if equipment and equipment != 공정.equipment:
#         계획변경이력.objects.create(
#             공정상세_fk=공정,
#             변경항목='equipment',
#             이전값=str(공정.equipment),
#             변경값=str(equipment)
#         )
#         공정.equipment = equipment
		
#     if 계획일 and 계획일 != 공정.계획일:
#         계획변경이력.objects.create(
#             공정상세_fk=공정,
#             변경항목='계획일',
#             이전값=str(공정.계획일),
#             변경값=str(계획일)
#         )
#         공정.계획일 = 계획일
	
#     공정.save()