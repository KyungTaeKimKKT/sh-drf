
import redis
import json
import time
from django.apps import apps
from celery import shared_task
from django.db import close_old_connections
from django.conf import settings
from pathlib import Path

def get_face_image_db_data(data:dict) -> dict:
    copyed = data.copy()
    image_path = copyed['image']
    if str(image_path).startswith(str(settings.MEDIA_ROOT)):
        # MEDIA_ROOT 경로 하위일 때만 상대경로 추출
        relative_path = str(Path(image_path).relative_to(settings.MEDIA_ROOT))
    else:
        # MEDIA_ROOT 밖이면 파일명만 저장 (또는 전체경로 그대로 저장)
        relative_path = Path(image_path).name
    copyed['image'] = relative_path
    copyed['is_증강'] = copyed['is_augmented']
    del copyed['is_augmented']
    return copyed    

def save_by_redisstream(job_id, redis_host=None, redis_port=None, redis_db=0):
    redis_host = redis_host or settings.REDIS_HOST
    redis_port = int(redis_port or settings.REDIS_PORT)
    redis_db = redis_db

    r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)

    events = r.xread({settings.SAVE_MODEL_REQUEST: 0}, count=1000, block=0)
    for steam_name, messages in events:
        for msg_id, msg_data in messages:
            try:
                # decode_responses=True면 key는 str
                payload = json.loads(msg_data['data'])
                model_path = payload['model_path']   # e.g., 'ai.face'
                data = payload['data']              # DB insert용 dict

                # Django model 가져오기
                app_name, model_name = model_path.rsplit('.', 1)
                model_class = apps.get_model(app_name, model_name)

                if model_name == 'FaceImage':
                    data = get_face_image_db_data(data)
                # DB 저장
                instance = None
                if 'id' in data:
                    try:
                        instance = model_class.objects.get(id=data['id'])
                        print(f"Updating ~~: instance: {instance}")
                    except model_class.DoesNotExist:
                        instance = model_class.objects.create(**data)
                else:
                    instance, created = model_class.objects.get_or_create(**data)

                # 속성 업데이트
                for k, v in data.items():
                    setattr(instance, k, v)
                instance.save()

                # 처리 완료 후 삭제
                r.xdel(settings.SAVE_MODEL_REQUEST, msg_id)

                # 마지막 처리 ID 갱신
                LAST_ID = msg_id

            except Exception as e:
                print(f"Error saving stream event: {e}")



def main_job(job_id):
    save_by_redisstream(job_id)

## from scheduler_job.jobs.db_save_by_redisstream import main_job