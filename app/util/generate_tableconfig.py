import util.utils_func as Utils


def generate_table_config_db(MODEL, div:str, name:str, serializer):

    TABLE_NAME = f"{div}_{name}_appID_{Utils.get_tableName_from_api권한(div=div, name=name)}"

    if (qs:= MODEL.objects.filter(table_name=TABLE_NAME) ):
        qs.delete()

    _isSuccess = Utils.generate_table_config_db( 
        table_name=TABLE_NAME, 
        model_field = Utils.get_MODEL_field_type(MODEL),
        serializer_field = Utils.get_Serializer_field_type( serializer ),
    )
    if _isSuccess:
        print ( f'{TABLE_NAME} 테이블 설정 생성 완료' )
    else:
        print ( f'{TABLE_NAME} 테이블 설정 생성 실패' )


def generate_table_config_db_by_ApiApp권한(MODEL, TABLE_NAME:str, serializer):


    if (qs:= MODEL.objects.filter(table_name=TABLE_NAME) ):
        qs.delete()

    _isSuccess = Utils.generate_table_config_db( 
        table_name=TABLE_NAME, 
        model_field = Utils.get_MODEL_field_type(MODEL),
        serializer_field = Utils.get_Serializer_field_type( serializer ),
    )
    if _isSuccess:
        print ( f'{TABLE_NAME} 테이블 설정 생성 완료' )
    else:
        print ( f'{TABLE_NAME} 테이블 설정 생성 실패' )