from  django.db import transaction
import time
from datetime import date, timedelta, datetime
from users import models as Users_Models

import logging, traceback
logger = logging.getLogger(__name__)

def snapshot_app_users() -> tuple[bool, dict]:
    try:
        with transaction.atomic():
            all_data = list(Users_Models.Api_App권한_User_M2M.objects.all().values('app_권한_id', 'user_id'))
            Users_Models.App권한_User_M2M_Snapshot.objects.create(
                data=all_data
            )
        return  True, {
            'log': f"snapshot_app_users 성공 : {len(all_data)} 건",
            'redis_publish': None
        }
    except Exception as e:
        logger.error(f"snapshot_app_users 실패 : {e}")
        logger.error(traceback.format_exc())
        return False, {
            'log': f"snapshot_app_users 실패 : {e}",
            'redis_publish': None
        }


def main_job(job_id:int):

	try:
		_isok, _log = snapshot_app_users()
			
		return  _log
	except Exception as e:
		logger.error(f"db_backup 실패 : {e}")
		logger.error(traceback.format_exc())
		return {
			'log': f"db_backup 실패 : {e}",
			'redis_publish': None
		}

