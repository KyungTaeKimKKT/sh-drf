from django.apps import AppConfig


class 생산모니터링Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '생산모니터링'

    # def ready(self):
    #     super().ready()

    #     if os.environ.get('RUN_MAIN', None) != 'true':            

    #         sched = BackgroundScheduler({'apscheduler.job_defaults.max_instances': 3})
    #         sched.add_job(  boradcast_생산모니터링, trigger='interval', seconds=1, id ='boradcast_생산모니터링' )
    #         sched.add_job ( api_기상청, trigger='cron', hour='6-22', minute='5', id='기상청')
    #         sched.start()
    #         api_기상청()

