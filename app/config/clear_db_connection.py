from django.db import connections
from psycopg2 import sql


def clear_db_connection():
    try:
        with connections['default'].cursor() as cursor:
            # 현재 세션을 제외한 나머지 idle 세션 종료
            cursor.execute("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = current_database()
                AND usename = current_user
                AND pid <> pg_backend_pid()
                AND state = 'idle';
            """)
        print("[config] DB connection cleared")
    except Exception as e:
        print(f"Error clearing db connection: {e}")