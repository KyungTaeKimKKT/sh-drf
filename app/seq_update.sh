#!/bin/bash

# 기본값
DB_NAME=""
DB_USER=""
DB_HOST="localhost"
DB_PORT="5432"

# 도움말 출력
print_help() {
    echo "사용법: $0 --name <DB이름> --user <사용자명> [--host <호스트>] [--port <포트>]"
    echo "예시:  ./seq_up.sh --name intranet --user myuser"
    exit 1
}

# 인자 파싱
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --name) DB_NAME="$2"; shift ;;
        --user) DB_USER="$2"; shift ;;
        --host) DB_HOST="$2"; shift ;;
        --port) DB_PORT="$2"; shift ;;
        -h|--help) print_help ;;
        *) echo "❌ 알 수 없는 인자: $1"; print_help ;;
    esac
    shift
done

# 필수 인자 확인
if [[ -z "$DB_NAME" || -z "$DB_USER" ]]; then
    echo "❗ DB 이름과 사용자명을 반드시 입력해야 합니다."
    print_help
fi

# 실행 메시지
echo "�� PostgreSQL 시퀀스를 업데이트합니다..."
echo "📂 DB: $DB_NAME"
echo "👤 사용자: $DB_USER"
echo "🌐 호스트: $DB_HOST"
echo "🔌 포트: $DB_PORT"

# PostgreSQL 명령 실행
psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" -v ON_ERROR_STOP=1 <<'EOSQL'
DO $$
DECLARE
    r RECORD;
    seq_name TEXT;
    full_table TEXT;
    sql TEXT;
BEGIN
    FOR r IN
        SELECT 
            table_schema,
            table_name,
            column_name
        FROM information_schema.columns
        WHERE column_default LIKE 'nextval%' 
        AND table_schema NOT IN ('pg_catalog', 'information_schema')
    LOOP
        -- 시퀀스 이름 가져오기
        SELECT pg_get_serial_sequence(
            quote_ident(r.table_schema) || '.' || quote_ident(r.table_name),
            r.column_name
        )
        INTO seq_name;

        -- 전체 테이블명
        full_table := quote_ident(r.table_schema) || '.' || quote_ident(r.table_name);

        -- 동적 SQL 생성
        sql := 'SELECT setval(' || quote_literal(seq_name) || ', COALESCE(MAX(' || 
               quote_ident(r.column_name) || '), 1), true) FROM ' || full_table;

        -- 실행
        EXECUTE sql;
    END LOOP;
END;
$$;
EOSQL

echo "✅ 모든 시퀀스가 최신 상태로 맞춰졌습니다."
