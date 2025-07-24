# PBN Backend API

FollowSales PBN 백링크 구축 서비스의 백엔드 API 서버입니다.

## 🚀 주요 기능

- **PBN 백링크 자동 구축**: 무료/유료 PBN 백링크 서비스
- **사용자 인증**: Clerk JWT 기반 인증 시스템
- **이메일 알림**: Resend API를 통한 자동 이메일 발송
- **작업 큐**: Celery + Redis를 통한 비동기 작업 처리
- **모니터링**: 작업 상태 추적 및 관리 대시보드
- **데이터베이스**: Supabase PostgreSQL 연동

## 🛠 기술 스택

- **Framework**: FastAPI
- **Database**: PostgreSQL (Supabase)
- **Queue**: Celery + Redis
- **Authentication**: Clerk JWT
- **Email**: Resend API
- **Deployment**: Docker + Cloudtype
- **Migration**: Alembic

## 📋 API 엔드포인트

### 인증
- `POST /api/v1/verify` - JWT 토큰 검증 및 사용자 등록
- `GET /api/v1/users/me` - 현재 사용자 정보 조회

### PBN 서비스
- `POST /api/v1/pbn/rest-test-request` - 무료 PBN 백링크 요청 (테스트용)
- `POST /api/v1/pbn/sample-request` - 무료 PBN 백링크 요청 (인증 필요)
- `GET /api/v1/pbn/check-free-usage` - 무료 PBN 사용 이력 확인
- `GET /api/v1/pbn/rest-orders/{order_id}/status` - 주문 상태 조회
- `POST /api/v1/pbn/admin/reset-free-usage/{clerk_id}` - 관리자용 무료 PBN 제한 해제

### 모니터링
- `GET /api/v1/monitoring/tasks/statistics` - 작업 통계
- `GET /api/v1/monitoring/system/health` - 시스템 상태 확인
- `GET /api/v1/monitoring/tasks/failed` - 실패한 작업 조회

## 🔐 무료 PBN 백링크 제한 정책

### 📋 **1회 제한 정책**
- **한 계정당 1회만** 무료 PBN 백링크 서비스 이용 가능
- 이미 사용한 계정은 자동으로 차단됩니다
- 추가 이용을 원하시면 유료 서비스를 이용해주세요

### 🔍 **사용 이력 확인**
```bash
# 현재 사용자의 무료 PBN 사용 가능 여부 확인
GET /api/v1/pbn/check-free-usage
Authorization: Bearer {clerk_jwt_token}
```

### ⚠️ **제한 적용 시 응답**

**개선된 사용자 친화적 에러 메시지:**
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

### 🧪 **테스트 계정 예외 처리**

**무제한 사용 가능한 테스트 계정:**
- `vnfm0580@gmail.com` (관리자 계정)
- `mwang12347890@gmail.com` (테스트 계정)

이 계정들은 무료 PBN 1회 제한에서 **자동으로 제외**되어 무제한 사용 가능합니다.

### 🛠 **관리자 제한 해제**
```bash
# 관리자가 특정 사용자의 무료 PBN 제한 해제
POST /api/v1/pbn/admin/reset-free-usage/{clerk_id}?reason=고객지원요청
Authorization: Bearer {admin_jwt_token}
```

## 🎨 프론트엔드 에러 처리 가이드

### **개선된 에러 응답 활용**

새로운 에러 응답 형태를 활용해 사용자 친화적인 UI를 구현할 수 있습니다:

```javascript
// API 요청 시 에러 처리 예제
try {
  const response = await fetch('/api/v1/pbn/sample-request', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwt_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      target_url: 'https://example.com',
      keyword: 'SEO 백링크'
    })
  });

  if (!response.ok) {
    const errorData = await response.json();
    
    if (errorData.detail?.code === 'FREE_PBN_ALREADY_USED') {
      // 보기 좋은 경고 팝업 표시
      showWarningModal({
        title: errorData.detail.title,
        message: errorData.detail.message,
        type: errorData.detail.type,
        recommendations: errorData.detail.recommendations,
        userInfo: errorData.detail.user_info
      });
    }
  }
} catch (error) {
  console.error('API 요청 실패:', error);
}
```

### **추천 UI 컴포넌트**

```html
<!-- 경고 모달 예제 -->
<div class="warning-modal">
  <div class="modal-header">
    <h3>⚠️ 무료 서비스 이용 제한</h3>
  </div>
  <div class="modal-body">
    <div class="user-info">
      <p><strong>📧 이메일:</strong> user@example.com</p>
      <p><strong>📊 이용 현황:</strong> 1회 사용 완료</p>
    </div>
    
    <div class="recommendations">
      <h4>💡 추천 서비스:</h4>
      <ul>
        <li>프리미엄 PBN 백링크 패키지</li>
        <li>고품질 백링크 서비스 상담</li>
        <li>맞춤형 SEO 전략 수립</li>
      </ul>
    </div>
  </div>
  <div class="modal-footer">
    <button class="btn-primary">프리미엄 서비스 보기</button>
    <button class="btn-secondary">문의하기</button>
    <button class="btn-close">닫기</button>
  </div>
</div>
```

### **테스트 계정 확인**

테스트 계정 여부는 응답의 `is_test_account` 필드로 확인할 수 있습니다:

```javascript
// 사용자 계정 상태 확인
const checkUserStatus = async () => {
  const response = await fetch('/api/v1/pbn/check-free-usage');
  const data = await response.json();
  
  if (data.is_test_account) {
    console.log('테스트 계정: 무제한 사용 가능');
    showTestAccountBadge();
  }
};
```

## 🐳 Docker로 실행

### 로컬 개발환경
```bash
# 저장소 클론
git clone https://github.com/woopsmarketing/pbn_mvp_backend.git
cd pbn_mvp_backend

# 환경변수 설정
cp .env.example .env
# .env 파일을 열어서 필요한 값들을 설정하세요

# Docker Compose로 실행
docker-compose up -d

# 마이그레이션 실행
docker-compose exec api alembic upgrade head
```

### 프로덕션 배포 (Cloudtype)
```bash
# Dockerfile을 사용하여 배포
# Cloudtype에서 환경변수를 설정하고 배포하세요
```

## 🔧 환경변수 설정

`.env` 파일에 다음 환경변수들을 설정해야 합니다:

```env
# 데이터베이스
DATABASE_URL=postgresql+psycopg2://user:password@host:port/dbname

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Clerk 인증
CLERK_SECRET_KEY=your_clerk_secret
CLERK_JWK_URL=your_jwk_url
CLERK_ISSUER=your_issuer
CLERK_AUDIENCE=your_audience

# 이메일 서비스
RESEND_API_KEY=your_resend_api_key
EMAIL_FROM=your_sender_email

# Celery & Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# 기타
SECRET_KEY=your_secret_key
DEBUG=false
```

## 📚 개발 가이드

### 로컬 개발 설정
```bash
# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션
alembic upgrade head

# 개발 서버 시작
uvicorn main:app --reload --port 8000

# Celery Worker 시작 (별도 터미널)
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo

# Celery Beat 시작 (별도 터미널)
celery -A app.tasks.celery_app beat --loglevel=info
```

### 새 마이그레이션 생성
```bash
alembic revision --autogenerate -m "migration description"
alembic upgrade head
```

## 🔍 API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📊 모니터링

- Flower (Celery 모니터링): `http://localhost:5555`
- 작업 통계 API: `/api/v1/monitoring/tasks/statistics`
- 시스템 상태: `/api/v1/monitoring/system/health`

## 🚀 배포

### Cloudtype 배포
1. GitHub 저장소를 Cloudtype에 연결
2. Dockerfile 배포 방식 선택
3. 환경변수 설정
4. 배포 실행

### 환경변수 설정 (Cloudtype)
Cloudtype 대시보드에서 위의 환경변수들을 모두 설정해주세요.

## 📝 라이센스

이 프로젝트는 MIT 라이센스를 따릅니다.

## 🤝 기여

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

- 이메일: vnfm0580@gmail.com
- GitHub: [woopsmarketing](https://github.com/woopsmarketing) 