from django.core.management.base import BaseCommand
from util.generate_tableconfig_from_app_auth import generate_table_configs_from_app_auth

class Command(BaseCommand):
    help = 'Api_App권한 테이블에 등록된 모든 앱에 대해 Table_Config를 생성합니다.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('테이블 설정 생성 시작...'))
        success, failed, skipped = generate_table_configs_from_app_auth()
        self.stdout.write(self.style.SUCCESS(f'처리 완료: 성공 {success}개, 실패 {failed}개, 건너뜀 {skipped}개')) 