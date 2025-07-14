# v1.0 - Celery 워커 엔트리포인트 (2024.07.03)
# 한글 주석: 이 파일은 Celery 워커 컨테이너의 진입점 역할을 합니다.
# 사용 예시: python -m app.tasks.celery_worker_entry

from app.tasks.celery_app import celery

if __name__ == "__main__":
    # 한글 주석: 워커 실행 (테스트 및 확장성 고려)
    celery.worker_main()
