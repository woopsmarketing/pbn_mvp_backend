# PBN Backend API

BacklinkVending PBN 백링크 구축 서비스의 백엔드 API 서버입니다.

## 🎯 주요 기능

### 🔗 PBN 백링크 서비스
- **무료 PBN 백링크 구축**: 계정당 1회 무료 이용 가능
- **PBN 사이트 관리**: 다양한 PBN 도메인을 통한 백링크 생성
- **키워드 최적화**: 지정한 키워드로 최적화된 백링크 생성
- **자동 콘텐츠 생성**: AI를 활용한 고품질 콘텐츠 자동 생성

### 📧 이메일 서비스
- **환영 이메일**: 신규 사용자 가입 시 자동 발송
- **주문 확인**: PBN 백링크 주문 접수 시 확인 이메일
- **완료 알림**: 백링크 구축 완료 시 결과 이메일
- **관리자 알림**: 시스템 오류 시 관리자 알림

### 👤 사용자 관리
- **Clerk 인증**: 안전한 사용자 인증 및 관리
- **무료 사용 제한**: 계정별 무료 서비스 이용 제한
- **테스트 계정**: 관리자 및 테스트 목적 계정 지원

## 🛠 기술 스택

### Backend Framework
- **FastAPI**: 고성능 Python 웹 프레임워크
- **Pydantic**: 데이터 검증 및 설정 관리
- **Uvicorn**: ASGI 서버

### Database & Storage
- **PostgreSQL**: 메인 데이터베이스 (Supabase)
- **Supabase**: 백엔드 서비스 및 실시간 기능
- **Redis**: 캐싱 및 세션 관리

### Task Queue
- **Celery**: 비동기 작업 처리
- **Redis**: Celery 브로커 및 결과 백엔드

### AI & Content Generation
- **OpenAI GPT**: 콘텐츠 자동 생성
- **LangChain**: AI 체인 및 프롬프트 관리

### External Services
- **Clerk**: 사용자 인증 및 관리
- **Resend**: 이메일 발송 서비스
- **WordPress**: PBN 사이트 콘텐츠 업로드

### DevOps
- **Docker**: 컨테이너화
- **CloudType**: 배포 및 호스팅

## 📁 프로젝트 구조

```
pbn-backend-cloudtype/
├── app/
│   ├── api/                    # API 라우터 및 엔드포인트
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── auth.py     # 사용자 인증
│   │           ├── pbn_rest.py # PBN 백링크 서비스
│   │           ├── users.py    # 사용자 관리
│   │           └── ...
│   ├── core/                   # 핵심 설정 및 구성
│   │   ├── config.py          # 환경 설정
│   │   ├── exceptions.py      # 커스텀 예외
│   │   └── ...
│   ├── db/                     # 데이터베이스 모델 및 세션
│   │   ├── models/            # SQLAlchemy 모델
│   │   └── session.py         # DB 세션 관리
│   ├── services/              # 비즈니스 로직 서비스
│   │   ├── email.py           # 이메일 서비스
│   │   ├── pbn_manager.py     # PBN 관리
│   │   └── ...
│   ├── tasks/                 # Celery 비동기 작업
│   │   ├── celery_app.py      # Celery 앱 설정
│   │   ├── email_tasks.py     # 이메일 작업
│   │   ├── pbn_tasks.py       # PBN 작업
│   │   └── ...
│   └── utils/                 # 유틸리티 함수
├── docker-compose.yml         # Docker 구성
├── requirements.txt           # Python 의존성
└── main.py                   # FastAPI 애플리케이션 진입점
```

## 🚀 API 엔드포인트

### PBN 백링크 서비스
- `POST /api/v1/pbn/rest-test-request` - 테스트용 PBN 백링크 요청
- `POST /api/v1/pbn/sample-request` - 무료 PBN 백링크 요청
- `GET /api/v1/pbn/check-free-usage` - 무료 사용 현황 확인
- `POST /api/v1/pbn/admin/reset-free-usage/{clerk_id}` - 관리자: 무료 사용 초기화

### 사용자 관리
- `POST /api/v1/auth/signup` - 사용자 회원가입
- `GET /api/v1/users/me` - 현재 사용자 정보 조회
- `GET /api/v1/users/{user_id}` - 특정 사용자 정보 조회

### 모니터링
- `GET /api/v1/monitoring/health` - 서비스 상태 확인
- `GET /api/v1/monitoring/celery` - Celery 워커 상태 확인

## 🔒 무료 PBN 백링크 제한 정책

### 기본 정책
- **이용 제한**: 한 계정당 1회만 무료 이용 가능
- **확인 방법**: 사용자의 Clerk ID 기반으로 이용 내역 추적
- **체크 API**: `/api/v1/pbn/check-free-usage`로 사용 가능 여부 확인

### 제한 적용 시 응답
```json
{
  "detail": {
    "success": false,
    "message": "⚠️ 무료 PBN 백링크 서비스 이용 제한\n\n안녕하세요!\n죄송하지만 무료 PBN 백링크 서비스는 한 계정당 1회만 이용하실 수 있습니다.\n\n📊 현재 이용 현황:\n• 이메일: user@example.com\n• 총 무료 주문: 1회\n• 진행 중인 주문: 1개\n\n💡 더 많은 백링크가 필요하시다면:\n• 프리미엄 PBN 백링크 패키지를 이용해주세요\n• 고품질의 다양한 백링크를 제공합니다\n• 문의사항은 언제든 연락주세요!\n\n감사합니다 🙏",
    "title": "무료 서비스 이용 제한",
    "type": "warning",
    "code": "FREE_PBN_ALREADY_USED",
    "user_info": {
      "email": "user@example.com",
      "total_orders": 1,
      "active_orders": 1
    },
    "recommendations": [
      "프리미엄 PBN 백링크 패키지 이용",
      "고품질 백링크 서비스 문의",
      "맞춤형 SEO 상담 신청"
    ]
  }
}
```

### 테스트 계정 예외 처리
다음 계정들은 무료 PBN 백링크 서비스 이용 제한에서 제외됩니다:

- **`vnfm0580@gmail.com`** (관리자 계정)
- **`mwang12347890@gmail.com`** (테스트 계정)

이 계정들은 무제한으로 무료 PBN 백링크 서비스를 이용할 수 있습니다.

### 프론트엔드 에러 처리 가이드

#### 에러 응답 처리
```javascript
// API 응답에서 무료 PBN 제한 에러 처리
if (errorData.detail?.code === 'FREE_PBN_ALREADY_USED') {
  // 사용자 친화적 팝업 표시
  showWarningModal({
    title: errorData.detail.title,
    message: errorData.detail.message,
    type: errorData.detail.type,
    recommendations: errorData.detail.recommendations
  });
}
```

#### 사용 가능 여부 확인
```javascript
// 무료 PBN 사용 가능 여부 사전 확인
const checkUsage = async () => {
  const response = await fetch('/api/v1/pbn/check-free-usage', {
    headers: { 'Authorization': `Bearer ${userToken}` }
  });
  const data = await response.json();
  
  if (data.is_test_account) {
    console.log('테스트 계정: 무제한 사용 가능');
  } else if (!data.can_use_free_pbn) {
    console.log('무료 서비스 이용 불가');
  }
};
```

## 🔧 설치 및 실행

### 1. 환경 변수 설정
`.env` 파일 생성 후 필요한 환경변수 설정:

```bash
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Clerk
CLERK_JWK_URL=your_clerk_jwk_url
CLERK_ISSUER=your_clerk_issuer

# Redis
REDIS_URL=redis://localhost:6379

# Email (Resend)
RESEND_API_KEY=your_resend_api_key
EMAIL_FROM=noreply@backlinkvending.com

# OpenAI
OPENAI_API_KEY=your_openai_api_key
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. Redis 서버 시작
```bash
redis-server
```

### 4. Celery 워커 시작
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

### 5. FastAPI 서버 시작
```bash
uvicorn main:app --reload
```

### 6. Docker로 실행 (선택사항)
```bash
docker-compose up -d
```

## 📧 이메일 서비스 설정

### Resend 설정
- **발신자**: `BacklinkVending 팀 <noreply@backlinkvending.com>`
- **도메인**: `backlinkvending.com` (DNS 인증 완료 필요)
- **템플릿**: 환영, 주문확인, 완료알림, 관리자알림

### 이메일 타입
1. **welcome**: 신규 사용자 환영 이메일
2. **order_confirmation**: 주문 접수 확인
3. **backlink_completion**: 백링크 구축 완료
4. **admin_alert**: 관리자 실패 알림
5. **backlink_report**: 백링크 현황 보고서

## 🔍 모니터링 및 로깅

### Health Check
- **FastAPI**: `/api/v1/monitoring/health`
- **Celery**: `/api/v1/monitoring/celery`
- **Redis**: 연결 상태 자동 확인

### 로깅
- **이메일 로그**: Supabase `email_logs` 테이블
- **작업 로그**: Celery 작업 결과 추적
- **에러 로그**: 시스템 에러 및 예외 상황

## 🔄 백그라운드 작업 (Celery)

### 이메일 작업
- `send_welcome_email`: 환영 이메일 발송
- `send_order_confirmation_email`: 주문 확인 이메일
- `send_backlink_completion_email`: 완료 알림 이메일

### PBN 작업
- `create_pbn_backlinks`: PBN 백링크 생성
- `generate_pbn_content`: AI 콘텐츠 생성
- `upload_to_wordpress`: WordPress 사이트 업로드

### 스케줄 작업
- **매일 09:00**: 일일 보고서 생성
- **매일 02:00**: 오래된 로그 정리
- **30분마다**: PBN 사이트 상태 확인

## 🐳 Docker 배포

### 개발 환경
```bash
docker-compose -f docker-compose.dev.yml up
```

### 프로덕션 환경
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### CloudType 배포
- **백엔드**: FastAPI 서버 자동 배포
- **워커**: Celery 워커 별도 컨테이너
- **모니터링**: 실시간 상태 확인

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

## 🤝 기여하기

1. Fork 프로젝트
2. Feature 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

## 📞 연락처

- **이메일**: noreply@backlinkvending.com
- **프로젝트**: BacklinkVending PBN 백링크 서비스

---

**BacklinkVending** - 고품질 PBN 백링크로 SEO 성과를 향상시키세요! 🚀 
