from .models import (
    디자인의뢰,
    의뢰file,
    완료file,
    Group의뢰
)
from users.models import Api_App권한

def _get_디자이너list() -> list[int]:
    return Api_App권한.objects.filter(div='디자인관리', name='완료')[0].user_pks
