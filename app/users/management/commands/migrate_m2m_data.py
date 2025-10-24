from django.core.management.base import BaseCommand
from users.models import Api_App권한, Api_App권한_User_M2M, User
from django.db import transaction

class Command(BaseCommand):
    help = 'Api_App권한의 M2M 관계를 새로운 중간 모델로 이전합니다'

    def handle(self, *args, **options):
        self.stdout.write('데이터 이전을 시작합니다...')
        
        # 트랜잭션으로 묶어 일관성 유지
        with transaction.atomic():
            # 모든 Api_App권한 객체를 가져옵니다
            app_권한_목록 = Api_App권한.objects.all()
            
            # 이전된 관계 수를 추적합니다
            이전_관계_수 = 0
            
            for app_권한 in app_권한_목록:
                # 현재 앱 권한에 연결된 모든 사용자를 가져옵니다
                연결된_사용자들 = app_권한.user_pks.all()
                
                # 각 사용자에 대해 새 중간 모델 레코드를 생성합니다
                for 사용자 in 연결된_사용자들:
                    # 이미 존재하는지 확인하여 중복 생성 방지
                    중간_모델, 생성됨 = Api_App권한_User_M2M.objects.get_or_create(
                        app_권한=app_권한,
                        user=사용자
                    )
                    
                    if 생성됨:
                        이전_관계_수 += 1
            
            self.stdout.write(self.style.SUCCESS(f'데이터 이전 완료! {이전_관계_수}개의 관계가 이전되었습니다.'))
            
            # 검증: 모든 관계가 올바르게 이전되었는지 확인
            총_m2m_관계_수 = sum(app.user_pks.count() for app in Api_App권한.objects.all())
            총_중간모델_관계_수 = Api_App권한_User_M2M.objects.count()
            
            if 총_m2m_관계_수 == 총_중간모델_관계_수:
                self.stdout.write(self.style.SUCCESS('검증 성공: 모든 관계가 올바르게 이전되었습니다.'))
            else:
                self.stdout.write(self.style.WARNING(
                    f'검증 경고: M2M 관계 수({총_m2m_관계_수})와 중간 모델 관계 수({총_중간모델_관계_수})가 일치하지 않습니다.'
                ))