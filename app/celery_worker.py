"""
Celery 워커 설정 및 실행
Windows 환경에서 최적화된 설정을 사용합니다.
"""

import os
import sys
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 필수 Supabase 환경변수 존재 여부 검증
required_env = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"]
missing = [e for e in required_env if not os.getenv(e)]

if missing:
    missing_str = ", ".join(missing)
    sys.stderr.write(
        f"[Celery Worker] ❌ .env에 다음 Supabase 변수가 없습니다: {missing_str}\n"
        "작업을 진행할 수 없으므로 워커를 종료합니다. 환경변수를 설정 후 다시 실행하세요.\n"
    )
    sys.exit(1)

# celery_app.py에서 통합된 Celery 앱을 import
from app.tasks.celery_app import celery as app

# 워커 실행을 위한 앱 참조
if __name__ == "__main__":
    app.start()
