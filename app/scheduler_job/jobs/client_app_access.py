from 모니터링.models import Client_App_Access_Log
from django.utils.timezone import now, timedelta
from users.models import User

from 모니터링.models import Client_App_Access_Log
from django.utils.timezone import now, timedelta
from users.models import User, Api_App권한

def aggregate_current_status():
    start_of_day = now().replace(hour=0, minute=0, second=0, microsecond=0)
    ordering = ['user_id__기본조직3', 'user_id__기본조직2', 'user_id__기본조직1', 'user_id', '-timestamp']

    # 오늘자 로그 중 사용자별 최신 로그만 추출
    recent_logs = Client_App_Access_Log.objects.filter(
        timestamp__gte=start_of_day
    ).order_by(*ordering)

    latest_logs_by_user = {}
    for log in recent_logs:
        if log.user_id not in latest_logs_by_user:
            latest_logs_by_user[log.user_id] = log

    # 사용자 전체 목록
    total_users_qs = User.objects.filter(is_active=True) #.exclude(id=1)
    total_users = total_users_qs.count()

    # 기본값 초기화
    online_users = 0
    running_users = 0
    offline_users = 0
    org_summary = {}      # 부서별 on/run/off

    app_running = {}  # 실행 중인 앱 수 기록
    all_app_id = {app.id for app in Api_App권한.objects.filter(is_Active=True, is_dev=False).order_by('순서')}  # 전체 앱 이름 확보

    # 사용자별 로그 상태 분류
    for user in total_users_qs:
        log = latest_logs_by_user.get(user.id)

        if not log or log.status == 'logout':
            status = 'offline'
            offline_users += 1
        elif log.status == 'running' and log.app_fk:
            status = 'running'
            running_users += 1
            app_id = log.app_fk.id
            app_running[app_id] = app_running.get(app_id, 0) + 1
        else:
            status = 'online'
            online_users += 1

        org = user.기본조직1 or "미지정"
        org_data = org_summary.setdefault(org, {"online": 0, "running": 0, "offline": 0})
        org_data[status] += 1

    # 전체 앱 목록 기준으로 0개도 포함시킴
    by_app_running = {app_id: app_running.get(app_id, 0) for app_id in all_app_id }


    return {
        "log": "client_api_access",
        "redis_publish": {
            "timestamp": now().isoformat(),
            "total_users": total_users,
            "online_users": online_users,
            "running_users": running_users,
            "offline_users": offline_users,
            "by_department": org_summary,
            "by_app_running": by_app_running,
        }
    }

def main_job(job_id:int):
    result = aggregate_current_status()
    print (result)
    return result

# from scheduler_job.jobs.client_api_access import main_job
# result = main_job(1)
# import pprint; pprint.pprint(result)