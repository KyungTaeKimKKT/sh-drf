from django.core.management.base import BaseCommand
from users.models import Api_App권한, Api_App권한_User_M2M, User

class Command(BaseCommand):
    help = 'M2M 데이터 이전이 올바르게 되었는지 확인합니다'

    def handle(self, *args, **options):
        self.stdout.write('데이터 이전 검증을 시작합니다...')
        
        # 모든 Api_App권한 객체를 가져옵니다
        app_권한_목록 = Api_App권한.objects.all()
        
        for app_권한 in app_권한_목록:
            # M2M 필드를 통한 사용자 목록
            m2m_사용자_ids = set(app_권한.user_pks.values_list('id', flat=True))
            
            # 중간 모델을 통한 사용자 목록
            중간모델_사용자_ids = set(
                Api_App권한_User_M2M.objects.filter(app_권한=app_권한).values_list('user_id', flat=True)
            )
            
            # 차이점 확인
            누락된_사용자 = m2m_사용자_ids - 중간모델_사용자_ids
            추가된_사용자 = 중간모델_사용자_ids - m2m_사용자_ids
            
            if not 누락된_사용자 and not 추가된_사용자:
                self.stdout.write(f'앱 권한 "{app_권한.name}": 모든 사용자 관계가 일치합니다.')
            else:
                if 누락된_사용자:
                    self.stdout.write(self.style.WARNING(
                        f'앱 권한 "{app_권한.name}": 중간 모델에 누락된 사용자 IDs: {누락된_사용자}'
                    ))
                if 추가된_사용자:
                    self.stdout.write(self.style.WARNING(
                        f'앱 권한 "{app_권한.name}": 중간 모델에 추가된 사용자 IDs: {추가된_사용자}'
                    ))
        
        self.stdout.write(self.style.SUCCESS('검증 완료!'))