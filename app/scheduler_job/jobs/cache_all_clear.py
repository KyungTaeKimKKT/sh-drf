from util.cache_manager import clear_all_cache

def main_job(job_id:int):
    clear_all_cache()
    return {
        'log': f"캐시 전체 삭제 완료",
        'redis_publish': None
    }