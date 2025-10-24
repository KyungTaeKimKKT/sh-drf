from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from django.utils import timezone
from users.models import User # custom User model import
from datetime import datetime, date

import uuid
import 생산지시.models as 생지

# from .생산계획_확정_brach import 확정_branch

class 생산계획_DDay(models.Model):
	_출하일 = models.IntegerField()
	_PO    = models.IntegerField()
	_판금  = models.IntegerField()
	_HI    = models.IntegerField()
	_구매  = models.IntegerField()
	_생지  = models.IntegerField()
	_작지  = models.IntegerField()

class 생산계획_일정관리(models.Model):
	생산지시_fk =  models.ForeignKey( 생지.생산지시 , on_delete=models.CASCADE, null=True, blank=True , related_name='생산지시_fk')
	is_계획반영_htm = models.BooleanField(default=False)
	is_계획반영_jamb = models.BooleanField(default=False)

	계획반영_htm_timestamp = models.DateTimeField(null=True, blank=True)
	계획반영_jamb_timestamp = models.DateTimeField(null=True, blank=True)

	납기일_Door = models.DateField(  blank=True, null=True)
	납기일_Cage = models.DateField(  blank=True, null=True)
	납기일_JAMB = models.DateField(  blank=True, null=True)

	### django-simple-history
	history = HistoricalRecords()

	def save(self, *args, **kwargs):
		if not self.pk and self.생산지시_fk and self.생산지시_fk.도면정보_fks.all().count() > 0:  # 새로운 인스턴스 생성 시에만
			self.납기일_Door = min( [ hogi.납기일_Door for hogi in self.생산지시_fk.도면정보_fks.all() if hogi and hasattr( hogi, '납기일_Door' ) ] )
			self.납기일_Cage = min( [ hogi.납기일_Cage for hogi in self.생산지시_fk.도면정보_fks.all() if hogi and hasattr( hogi, '납기일_Cage' ) ] )
		super().save(*args, **kwargs)


class 생산계획_확정_Branch(models.Model):
	""" 생산계획관리에서  확정되면 save 될때 DB DATA생성함"""
	생산계획관리_fk = models.ForeignKey(생산계획_일정관리, on_delete=models.CASCADE, null=True, blank=True)
	제품분류 = models.CharField(max_length=20,  null=True, blank=True)
	최종납기일 =  models.DateField(  blank=True, null=True)
	생산지시_process_fk = models.ForeignKey(생지.Process, on_delete=models.CASCADE, null=True, blank=True )
	공정 = models.CharField(max_length=20,  null=True, blank=True)
	공정_완료계획일 = models.DateField(  blank=True, null=True)
	작업명 = models.CharField(max_length=100,  null=True, blank=True) 
	계획수량 = models.IntegerField(null=True, blank=True)

	계획등록_timestamp = models.DateTimeField(default=timezone.now())
	is_Active = models.BooleanField( blank=True, null=True )

		### django-simple-history
	history = HistoricalRecords()

# class History(models.Model):
#     생산계획관리_fk = models.ForeignKey( 생산계획관리, on_delete=models.CASCADE, null=True, blank=True)
#     변경자 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True )
#     변경일자 = models.DateTimeField(default=timezone.now() )
#     변경내용 = models.TextField ( null=True, blank=True )