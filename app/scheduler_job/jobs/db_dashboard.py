from django.conf import settings
import psycopg2
import json, time

def db_status():
    """
    PostgreSQL 핵심 상태 조회
    1. Connections
    2. Transactions per second
    3. Block IO
    4. Max connections
    """
    try:
        s = time.perf_counter()
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
        )
        cur = conn.cursor()

        # 1️⃣ Connections 상태
        cur.execute("""
            SELECT state, COUNT(*) 
            FROM pg_stat_activity 
            GROUP BY state
        """)
        result = cur.fetchall()
        raw = []
        for state, count in result:
            # state가 None이면 idle로 통일
            state_name = state or 'idle'
            raw.append({'state': state_name, 'count': count})
        # 통일 및 합산
        connections = {}
        for row in raw:
            state = row['state'] or 'idle'
            connections[state] = connections.get(state, 0) + row['count']
        # 최종 리스트
        connections_list = [{'state': k, 'count': v} for k, v in connections.items()]

        # 2️⃣ Transactions per second (총 tx / 초)
        cur.execute("""
            SELECT sum(xact_commit + xact_rollback) as total_tx
            FROM pg_stat_database
        """)
        # total_tx는 None이면 0, Decimal이면 int 변환
        total_tx_raw = cur.fetchone()[0]
        total_tx = int(total_tx_raw) if total_tx_raw is not None else 0

        # 단순히 TPS로 계산하려면, 이전 호출 시점과 diff를 사용
        # 여기서는 그냥 현재 누적 수 제공

        # 3️⃣ Block IO (블록 읽기/쓰기)
        cur.execute("SELECT sum(blks_read) as blks_read, sum(blks_hit) as blks_hit FROM pg_stat_database")
        # 블록 IO도 마찬가지
        blks_read_raw, blks_hit_raw = cur.fetchone()
        blks_read = int(blks_read_raw) if blks_read_raw is not None else 0
        blks_hit = int(blks_hit_raw)  if blks_hit_raw is not None else 0
        block_io = {
            'blks_read' : blks_read,
            'blks_hit'  : blks_hit
        }

        # 4️⃣ Max connections
        cur.execute("SHOW max_connections")
        max_connections = int(cur.fetchone()[0])

        cur.close()
        conn.close()

        elapsed_ms = int((time.perf_counter() - s) * 1000)
        
        redis_publish = {
                'connections': connections_list ,
                'total_tx': total_tx,
                'block_io': block_io,
                'max_connections':max_connections
            }

        # print ( json.dumps( {'redis_publish': redis_publish}))
        return {
            'log': f"DB 상태 조회 완료 : connections={len(connections)}, tx={total_tx}, block IO(read/hit)={blks_read}/{blks_hit}, 소요시간={elapsed_ms}ms",
            'redis_publish': redis_publish
            # 'help_text': {
            #     'connections': "현재 DB 세션 상태: active = 실행중, idle = 대기중, total = 전체 세션 수",
            #     'total_tx': "데이터베이스 전체 트랜잭션 누적 수 (commit + rollback)",
            #     'block_io': "블록 읽기/캐시 hit 정보: blks_read = 디스크에서 읽은 블록, blks_hit = shared buffer hit"
            # }
        }
    except Exception as e:
        print(f"broadcast_db_status 오류: {e}")
        return {
            'log': f'error 발생: {str(e)}',
            'redis_publish' : {}
                }
    
def main_job(job_id:int):
    return db_status()


## from scheduler_job.jobs.db_dashboard import db_status, main_job