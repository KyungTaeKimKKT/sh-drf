from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone
from datetime import datetime
from 생산모니터링.models_외부 import 생산계획실적

class Command(BaseCommand):
    help = '생산계획실적 테이블의 중복 데이터를 삭제합니다.'

    def handle(self, *args, **options):
        self.stdout.write('중복 데이터 삭제 시작...')
        삭제된_항목_수, 유지된_항목_수 = self.생산계획실적_중복_삭제()
        self.stdout.write(self.style.SUCCESS(f'총 결과: {삭제된_항목_수}개 항목 삭제됨, {유지된_항목_수}개 항목 유지됨'))

    def 생산계획실적_중복_삭제(self):
        # 2025년 3월 30일 날짜 설정 (타임존 없이)
        시작날짜 = datetime(2025, 3, 30, 0, 0, 0)
        오늘 = timezone.now()
        
        self.stdout.write(f"기간: {시작날짜.strftime('%Y-%m-%d')} ~ {오늘.strftime('%Y-%m-%d')}")
        
        # 중복 데이터 찾기 (sensor_id, line_no, start_time, end_time이 동일한 데이터)
        중복_그룹 = 생산계획실적.objects.using('생산모니터링').filter(생성시간__gte=시작날짜, 생성시간__lte=오늘)\
            .values('sensor_id', 'line_no', 'start_time', 'end_time')\
            .annotate(count=models.Count('id'))\
            .filter(count__gt=1)
        
        self.stdout.write(f"발견된 중복 그룹 수: {중복_그룹.count()}")

        삭제된_항목_수 = 0
        유지된_항목_수 = 0
        
        # 각 중복 그룹에 대해 처리
        for 그룹 in 중복_그룹:
            # 해당 그룹의 모든 레코드 가져오기
            중복_레코드들 = 생산계획실적.objects.using('생산모니터링').filter(
                sensor_id=그룹['sensor_id'],
                line_no=그룹['line_no'],
                start_time=그룹['start_time'],
                end_time=그룹['end_time'],
                생성시간__gte=시작날짜,
                생성시간__lte=오늘
            )
            
            # plan_qty가 있는 레코드만 필터링
            plan_qty_있는_레코드들 = 중복_레코드들.filter(plan_qty__gt=0)
            
            # 유지할 레코드 결정
            if plan_qty_있는_레코드들.exists():
                # plan_qty가 있는 것 중 생성시간이 가장 늦은 것 선택
                유지할_레코드 = plan_qty_있는_레코드들.order_by('-생성시간').first()
            else:
                # plan_qty가 없는 경우 생성시간이 가장 늦은 것 선택
                유지할_레코드 = 중복_레코드들.order_by('-생성시간').first()
            
            # 유지할 레코드를 제외한 나머지 삭제
            삭제할_레코드들 = 중복_레코드들.exclude(id=유지할_레코드.id)
            삭제_수 = 삭제할_레코드들.count()
            삭제할_레코드들.delete()
            
            삭제된_항목_수 += 삭제_수
            유지된_항목_수 += 1
            
            self.stdout.write(f"그룹 {그룹['sensor_id']}, {그룹['line_no']}, {그룹['start_time']}, {그룹['end_time']} - "
                  f"{삭제_수}개 삭제됨, ID {유지할_레코드.id} 유지됨")
        
        return 삭제된_항목_수, 유지된_항목_수