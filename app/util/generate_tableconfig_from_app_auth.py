import importlib
from django.apps import apps
from users.models import Api_App권한
from util.generate_tableconfig import generate_table_config_db_by_ApiApp권한
import util.utils_func as Utils
from config.models import Table, Table_Config
import traceback

def get_model_and_serializer(model_path, serializer_path):
    """
    문자열 경로에서 모델과 시리얼라이저 객체를 가져옵니다.
    
    Args:
        model_path: 'app_name.ModelName' 형식의 모델 경로
        serializer_path: 'app_name.SerializerName' 형식의 시리얼라이저 경로
        
    Returns:
        (model_class, serializer_instance) 튜플 또는 오류 시 (None, None)
    """
    try:
        if not model_path:
            return None, None
            
        # 모델 가져오기
        app_name, model_name = model_path.rsplit('.', 1)
        model_class = apps.get_model(app_name, model_name)
        
        # 시리얼라이저 가져오기
        serializer_instance = None
        if serializer_path:
            app_name, serializer_name = serializer_path.rsplit('.', 1)
            module_path = f"{app_name}.serializers"
            serializers_module = importlib.import_module(module_path)
            serializer_class = getattr(serializers_module, serializer_name)
            serializer_instance = serializer_class()
            
        return model_class, serializer_instance
    except Exception as e:
        print(f"오류 발생: {e}")
        return None, None

def create_table_config(app_auth_instance:Api_App권한, table_instance:Table):
    """ kwargs:
        app_auth_instance: Api_App권한
        table_instance: Table
    """
    if not (app_auth_instance.TO_MODEL and app_auth_instance.TO_Serializer):
        return False

    model_class, serializer_instance = get_model_and_serializer(
        app_auth_instance.TO_MODEL, 
        app_auth_instance.TO_Serializer
    )

    if not model_class:
        print(f"  - 실패: 모델을 찾을 수 없습니다: {app_auth_instance.TO_MODEL}")
        return False
    
    try:
        TABLE_NAME = table_instance.table_name
        ### 기존 테이블 설정 삭제
        Table_Config.objects.filter(table=table_instance).delete()

        ### 테이블 설정 생성
        result = Utils.generate_table_config_db(
            table_instance=table_instance,
            model_field = Utils.get_MODEL_field_type(model_class),
            serializer_field = Utils.get_Serializer_field_type( serializer_instance ),
        )

        if result:
            print(f"  - 성공: {app_auth_instance.div}_{app_auth_instance.name} 테이블 설정 생성 완료")
            return True
        else:
            print(f"  - 실패: {app_auth_instance.div}_{app_auth_instance.name} 테이블 설정 생성 실패")  
            return False
    except Exception as e:
        print(f"  - 오류: {app_auth_instance.div}_{app_auth_instance.name} 처리 중 예외 발생: {e}")
        traceback.print_exc()
        return False


def generate_table_configs_from_app_auth():
    """Api_App권한 테이블에 등록된 모든 앱에 대해 Table_Config를 생성합니다."""
    
    # 활성화된 앱 권한만 가져오기
    app_auths = Api_App권한.objects.all()
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for app_auth in app_auths:
        print(f"\n처리 중: {app_auth.표시명_구분} - {app_auth.표시명_항목}")
        
        # TO_MODEL이 없으면 건너뛰기
        if not app_auth.TO_MODEL:
            print(f"  - 건너뜀: TO_MODEL이 지정되지 않았습니다.")
            skipped_count += 1
            continue
            
        # 모델과 시리얼라이저 가져오기
        model_class, serializer_instance = get_model_and_serializer(
            app_auth.TO_MODEL, 
            app_auth.TO_Serializer
        )
        
        if not model_class:
            print(f"  - 실패: 모델을 찾을 수 없습니다: {app_auth.TO_MODEL}")
            failed_count += 1
            continue
            
        # Table_Config 생성
        try:
            TABLE_NAME = f"{app_auth.div}_{app_auth.name}_appID_{app_auth.id}"
            from config.models import Table
            table_instance, created = Table.objects.get_or_create(table_name=TABLE_NAME)

            import util.utils_func as Utils
            import config.models as Config_Models
            if (qs:= Config_Models.Table_Config.objects.filter(table_name=TABLE_NAME) ):
                qs.delete()

            result = Utils.generate_table_config_db(
                table_instance=table_instance,
                model_field = Utils.get_MODEL_field_type(model_class),
                serializer_field = Utils.get_Serializer_field_type( serializer_instance ),
            )

            if result:
                success_count += 1
                print(f"  - 성공: {app_auth.div}_{app_auth.name} 테이블 설정 생성 완료")
            else:
                failed_count += 1
                print(f"  - 실패: {app_auth.div}_{app_auth.name} 테이블 설정 생성 실패")
        except Exception as e:
            failed_count += 1
            print(f"  - 오류: {app_auth.div}_{app_auth.name} 처리 중 예외 발생: {e}")
            traceback.print_exc()

    print(f"\n처리 완료: 성공 {success_count}개, 실패 {failed_count}개, 건너뜀 {skipped_count}개")
    return success_count, failed_count, skipped_count

if __name__ == "__main__":
    generate_table_configs_from_app_auth()