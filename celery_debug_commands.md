# Celery 디버깅 실전 조치 명령어 모음

## 1. 큐 이름 불일치 확인

### 워커 실행 시 큐 확인
```bash
# 현재 워커가 어떤 큐를 리스닝하는지 확인
celery -A app.tasks.celery_app worker --loglevel=info

# 특정 큐만 리스닝
celery -A app.tasks.celery_app worker --loglevel=info -Q default
celery -A app.tasks.celery_app worker --loglevel=info -Q celery
```

### FastAPI에서 큐 파라미터 테스트
```python
# 다양한 큐 이름으로 테스트
send_order_confirmation_email.apply_async(args=[...], queue="default")
send_order_confirmation_email.apply_async(args=[...], queue="celery")
send_order_confirmation_email.apply_async(args=[...])  # 기본 큐
```

## 2. Redis에 Task가 쌓이는지 확인

### Redis CLI 접속 (Cloudtype 환경)
```bash
# Redis 컨테이너 접속
redis-cli -h svc.sel4.cloudtype.app -p 31188

# 또는 Redis URL로 접속
redis-cli -u redis://svc.sel4.cloudtype.app:31188/0
```

### Redis에서 큐 상태 확인
```redis
# 큐 길이 확인
LLEN default
LLEN celery
LLEN email
LLEN pbn

# 큐 내용 확인 (처음 5개)
LRANGE default 0 4
LRANGE celery 0 4

# 모든 키 확인
KEYS *

# 큐 비우기 (테스트용)
DEL default
DEL celery
```

## 3. 네트워크/방화벽 확인

### 환경 변수 확인 스크립트
```bash
# FastAPI 컨테이너에서
python3 -c "
import os
print('CELERY_BROKER_URL:', os.getenv('CELERY_BROKER_URL'))
print('CELERY_RESULT_BACKEND:', os.getenv('CELERY_RESULT_BACKEND'))
"

# Celery 워커 컨테이너에서도 동일하게 실행
```

### 네트워크 연결 테스트
```bash
# FastAPI 컨테이너에서 Redis 연결 테스트
python3 -c "
import redis
r = redis.from_url('redis://svc.sel4.cloudtype.app:31188/0')
print('Redis 연결 테스트:', r.ping())
"

# Celery 워커 컨테이너에서도 동일하게 실행
```

## 4. 워커 상태 확인

### 워커 프로세스 확인
```bash
# 워커 프로세스 확인
ps aux | grep celery

# 워커 상태 확인
celery -A app.tasks.celery_app inspect active
celery -A app.tasks.celery_app inspect registered
celery -A app.tasks.celery_app inspect stats
```

### 워커 로그 레벨 높이기
```bash
# 더 상세한 로그로 워커 실행
celery -A app.tasks.celery_app worker --loglevel=debug

# 특정 로거만 활성화
celery -A app.tasks.celery_app worker --loglevel=info --logfile=/tmp/celery.log
```

## 5. 디버깅 스크립트 실행

### 종합 디버깅 스크립트
```bash
# FastAPI 컨테이너에서
python3 debug_celery.py

# Celery 워커 컨테이너에서도 실행
python3 debug_celery.py
```

### 개별 테스트
```bash
# Redis 연결만 테스트
python3 -c "
import redis
import os
r = redis.from_url(os.getenv('CELERY_BROKER_URL'))
print('Redis 연결:', r.ping())
print('default 큐 길이:', r.llen('default'))
print('celery 큐 길이:', r.llen('celery'))
"

# Celery 앱 임포트 테스트
python3 -c "
from app.tasks.celery_app import celery as app
print('등록된 태스크:', list(app.tasks.keys()))
"
```

## 6. 실시간 모니터링

### Celery 모니터링 도구
```bash
# Celery 이벤트 모니터링
celery -A app.tasks.celery_app events

# Celery 모니터 (웹 인터페이스)
celery -A app.tasks.celery_app monitor

# 실시간 로그 확인
tail -f /tmp/celery.log
```

### Redis 모니터링
```redis
# Redis 실시간 모니터링
MONITOR

# 특정 키 변화 감지
SUBSCRIBE __keyspace@0__:default
```

## 7. 테스트 태스크 실행

### 간단한 테스트 태스크
```python
# Python 스크립트로 테스트
from app.tasks.celery_app import celery as app

@app.task
def test_task(message):
    print(f"테스트 태스크 실행: {message}")
    return f"완료: {message}"

# 태스크 실행
result = test_task.apply_async(args=["Hello World"], queue="default")
print(f"태스크 ID: {result.id}")
```

### 실제 태스크 테스트
```python
# 실제 이메일 태스크 테스트
from app.tasks.email_tasks import send_order_confirmation_email

result = send_order_confirmation_email.apply_async(
    args=["test@example.com", "TEST-ORDER-123", {"target_url": "https://example.com", "keyword": "test"}],
    queue="default"
)
print(f"이메일 태스크 ID: {result.id}")
```

## 8. 문제 해결 체크리스트

### 1단계: 기본 확인
- [ ] Redis 연결 가능한지 확인
- [ ] 환경 변수 CELERY_BROKER_URL, CELERY_RESULT_BACKEND 일치하는지 확인
- [ ] 워커가 실행 중인지 확인

### 2단계: 큐 확인
- [ ] Redis에 태스크가 쌓이는지 확인 (LLEN default)
- [ ] 워커가 올바른 큐를 리스닝하는지 확인
- [ ] 큐 이름이 일치하는지 확인 (default vs celery)

### 3단계: 태스크 등록 확인
- [ ] 태스크가 Celery 앱에 등록되었는지 확인
- [ ] 태스크 함수 임포트 에러가 없는지 확인
- [ ] 순환 임포트 문제가 없는지 확인

### 4단계: 네트워크 확인
- [ ] FastAPI와 워커 컨테이너 간 네트워크 연결 확인
- [ ] 방화벽 설정 확인
- [ ] DNS 해석 문제 확인

### 5단계: 로그 분석
- [ ] 워커 로그에서 태스크 수신 여부 확인
- [ ] 에러 메시지 분석
- [ ] 태스크 실행 중 예외 발생 여부 확인

## 9. 긴급 해결 방법

### 워커 재시작
```bash
# 워커 프로세스 종료
pkill -f celery

# 워커 재시작
celery -A app.tasks.celery_app worker --loglevel=info --detach
```

### Redis 큐 초기화
```redis
# 모든 큐 비우기
FLUSHDB

# 특정 큐만 비우기
DEL default
DEL celery
```

### 강제 태스크 실행
```python
# 비동기 큐 대신 동기 실행
from app.tasks.email_tasks import send_order_confirmation_email
result = send_order_confirmation_email("test@example.com", "TEST-123", {"target_url": "https://example.com", "keyword": "test"})
``` 