

import json
from django.apps import apps

from django.conf import settings
from pathlib import Path
import os

def get_absolute_path(relative_path: str) -> str:
    return os.path.join(settings.MEDIA_ROOT, relative_path)

def get_relative_path(full_path: str) -> str:
    """
    MEDIA_ROOT 기준 상대 경로 반환
    """
    full_path = Path(full_path)
    media_root = Path(settings.MEDIA_ROOT)
    try:
        return str(full_path.relative_to(media_root))
    except ValueError:
        # MEDIA_ROOT 밖이면 파일명만 반환
        return full_path.name

def get_media_url(relative_path: str) -> str:
    if settings.MEDIA_URL not in relative_path:
        return os.path.join(settings.MEDIA_URL, relative_path)
    return relative_path

def get_face_image_db_data(data:dict) -> dict:
    ### 기존 등록되어 있으면 그냥 반환
    if 'id' in data:
        return data
    copyed = data.copy()
    image_path = copyed['image']        ### 상대경로임.
    # if str(image_path).startswith(str(settings.MEDIA_ROOT)):
    #     # MEDIA_ROOT 경로 하위일 때만 상대경로 추출
    #     relative_path = str(Path(image_path).relative_to(settings.MEDIA_ROOT))
    # else:
    #     # MEDIA_ROOT 밖이면 파일명만 저장 (또는 전체경로 그대로 저장)
    #     relative_path = Path(image_path).name
    if not os.path.exists( get_absolute_path(image_path)):
        print(f"Error: {image_path} not found")
    copyed['is_증강'] = copyed['is_augmented']
    del copyed['is_augmented']
    return copyed    

def save_from_rpc_response(rpc_response) -> dict:
    """
    rpc_response: face_register_pb2.FaceRegisterReply (또는 FaceRegisterResponse)
    """

    for event in rpc_response.data:  # repeated StreamEvent
        try:
            model_path = event.model_path
            data = dict(event.data)   # map<string, string> → dict
            app_name, model_name = model_path.rsplit('.', 1)

            model_class = apps.get_model(app_name, model_name)

            # FaceImage 특수 처리
            if model_name == "FaceImage":
                data = get_face_image_db_data(data)

            # JSON 직렬화된 embedding은 파싱 필요
            if "embedding" in data and isinstance(data["embedding"], str):
                try:
                    data["embedding"] = json.loads(data["embedding"])
                except Exception:
                    pass  # 그냥 문자열로 저장 가능

            # DB insert/update
            instance = None
            if "id" in data:
                try:
                    instance = model_class.objects.get(id=int(data["id"]))
                    print(f"Updating {model_name} id={data['id']}")
                except model_class.DoesNotExist:
                    instance = model_class.objects.create(**data)
            else:
                instance = model_class.objects.create(**data)

            # 필드 값 갱신
            for k, v in data.items():
                setattr(instance, k, v)
            instance.save()

        except Exception as e:
            print(f"Error saving rpc event: {e}")
            return { 'status': 'failed', 'detail': f'{e}' }

    return { 'status': 'success', 'detail': f'{len(rpc_response.data)} 개 저장 완료' }
