# PBN Backend API

BacklinkVending PBN 백링??구축 ?�비?�의 백엔??API ?�버?�니??

## ?? 주요 기능

- **PBN 백링???�동 구축**: 무료/?�료 PBN 백링???�비??
- **?�용???�증**: Clerk JWT 기반 ?�증 ?�스??
- **?�메???�림**: Resend API�??�한 ?�동 ?�메??발송
- **?�업 ??*: Celery + Redis�??�한 비동�??�업 처리
- **모니?�링**: ?�업 ?�태 추적 �?관�??�?�보??
- **?�이?�베?�스**: Supabase PostgreSQL ?�동

## ?�� 기술 ?�택

- **Framework**: FastAPI
- **Database**: PostgreSQL (Supabase)
- **Queue**: Celery + Redis
- **Authentication**: Clerk JWT
- **Email**: Resend API
- **Deployment**: Docker + Cloudtype
- **Migration**: Alembic

## ?�� API ?�드?�인??

### ?�증
- `POST /api/v1/verify` - JWT ?�큰 검�?�??�용???�록
- `GET /api/v1/users/me` - ?�재 ?�용???�보 조회

### PBN ?�비??
- `POST /api/v1/pbn/rest-test-request` - 무료 PBN 백링???�청 (?�스?�용)
- `POST /api/v1/pbn/sample-request` - 무료 PBN 백링???�청 (?�증 ?�요)
- `GET /api/v1/pbn/check-free-usage` - 무료 PBN ?�용 ?�력 ?�인
- `GET /api/v1/pbn/rest-orders/{order_id}/status` - 주문 ?�태 조회
- `POST /api/v1/pbn/admin/reset-free-usage/{clerk_id}` - 관리자??무료 PBN ?�한 ?�제

### 모니?�링
- `GET /api/v1/monitoring/tasks/statistics` - ?�업 ?�계
- `GET /api/v1/monitoring/system/health` - ?�스???�태 ?�인
- `GET /api/v1/monitoring/tasks/failed` - ?�패???�업 조회

## ?�� 무료 PBN 백링???�한 ?�책

### ?�� **1???�한 ?�책**
- **??계정??1?�만** 무료 PBN 백링???�비???�용 가??
- ?��? ?�용??계정?� ?�동?�로 차단?�니??
- 추�? ?�용???�하?�면 ?�료 ?�비?��? ?�용?�주?�요

### ?�� **?�용 ?�력 ?�인**
```bash
# ?�재 ?�용?�의 무료 PBN ?�용 가???��? ?�인
GET /api/v1/pbn/check-free-usage
Authorization: Bearer {clerk_jwt_token}
```

### ?�️ **?�한 ?�용 ???�답**

**개선???�용??친화???�러 메시지:**
```json
{
  "detail": {
    "success": false,
    "message": "?�️ 무료 PBN 백링???�비???�용 ?�한\n\n?�녕?�세??\n죄송?��?�?무료 PBN 백링???�비?�는 ??계정??1?�만 ?�용?�실 ???�습?�다.\n\n?�� ?�재 ?�용 ?�황:\n???�메?? user@example.com\n??�?무료 주문: 1??n??진행 중인 주문: 1�?n\n?�� ??많�? 백링?��? ?�요?�시?�면:\n???�리미엄 PBN 백링???�키지�??�용?�주?�요\n??고품질의 ?�양??백링?��? ?�공?�니??n??문의?�항?� ?�제???�락주세??\n\n감사?�니???��",
    "title": "무료 ?�비???�용 ?�한",
    "type": "warning",
    "code": "FREE_PBN_ALREADY_USED",
    "user_info": {
      "email": "user@example.com",
      "total_orders": 1,
      "active_orders": 1
    },
    "recommendations": [
      "?�리미엄 PBN 백링???�키지 ?�용",
      "고품�?백링???�비??문의",
      "맞춤??SEO ?�담 ?�청"
    ]
  }
}
```

### ?�� **?�스??계정 ?�외 처리**

**무제???�용 가?�한 ?�스??계정:**
- `vnfm0580@gmail.com` (관리자 계정)
- `mwang12347890@gmail.com` (?�스??계정)

??계정?��? 무료 PBN 1???�한?�서 **?�동?�로 ?�외**?�어 무제???�용 가?�합?�다.

### ?�� **관리자 ?�한 ?�제**
```bash
# 관리자가 ?�정 ?�용?�의 무료 PBN ?�한 ?�제
POST /api/v1/pbn/admin/reset-free-usage/{clerk_id}?reason=고객지?�요�?
Authorization: Bearer {admin_jwt_token}
```

## ?�� ?�론?�엔???�러 처리 가?�드

### **개선???�러 ?�답 ?�용**

?�로???�러 ?�답 ?�태�??�용???�용??친화?�인 UI�?구현?????�습?�다:

```javascript
// API ?�청 ???�러 처리 ?�제
try {
  const response = await fetch('/api/v1/pbn/sample-request', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwt_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      target_url: 'https://example.com',
      keyword: 'SEO 백링??
    })
  });

  if (!response.ok) {
    const errorData = await response.json();
    
    if (errorData.detail?.code === 'FREE_PBN_ALREADY_USED') {
      // 보기 좋�? 경고 ?�업 ?�시
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
  console.error('API ?�청 ?�패:', error);
}
```

### **추천 UI 컴포?�트**

```html
<!-- 경고 모달 ?�제 -->
<div class="warning-modal">
  <div class="modal-header">
    <h3>?�️ 무료 ?�비???�용 ?�한</h3>
  </div>
  <div class="modal-body">
    <div class="user-info">
      <p><strong>?�� ?�메??</strong> user@example.com</p>
      <p><strong>?�� ?�용 ?�황:</strong> 1???�용 ?�료</p>
    </div>
    
    <div class="recommendations">
      <h4>?�� 추천 ?�비??</h4>
      <ul>
        <li>?�리미엄 PBN 백링???�키지</li>
        <li>고품�?백링???�비???�담</li>
        <li>맞춤??SEO ?�략 ?�립</li>
      </ul>
    </div>
  </div>
  <div class="modal-footer">
    <button class="btn-primary">?�리미엄 ?�비??보기</button>
    <button class="btn-secondary">문의?�기</button>
    <button class="btn-close">?�기</button>
  </div>
</div>
```

### **?�스??계정 ?�인**

?�스??계정 ?��????�답??`is_test_account` ?�드�??�인?????�습?�다:

```javascript
// ?�용??계정 ?�태 ?�인
const checkUserStatus = async () => {
  const response = await fetch('/api/v1/pbn/check-free-usage');
  const data = await response.json();
  
  if (data.is_test_account) {
    console.log('?�스??계정: 무제???�용 가??);
    showTestAccountBadge();
  }
};
```

## ?�� Docker�??�행

### 로컬 개발?�경
```bash
# ?�?�소 ?�론
git clone https://github.com/woopsmarketing/pbn_mvp_backend.git
cd pbn_mvp_backend

# ?�경변???�정
cp .env.example .env
# .env ?�일???�어???�요??값들???�정?�세??

# Docker Compose�??�행
docker-compose up -d

# 마이그레?�션 ?�행
docker-compose exec api alembic upgrade head
```

### ?�로?�션 배포 (Cloudtype)
```bash
# Dockerfile???�용?�여 배포
# Cloudtype?�서 ?�경변?��? ?�정?�고 배포?�세??
```

## ?�� ?�경변???�정

`.env` ?�일???�음 ?�경변?�들???�정?�야 ?�니??

```env
# ?�이?�베?�스
DATABASE_URL=postgresql+psycopg2://user:password@host:port/dbname

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Clerk ?�증
CLERK_SECRET_KEY=your_clerk_secret
CLERK_JWK_URL=your_jwk_url
CLERK_ISSUER=your_issuer
CLERK_AUDIENCE=your_audience

# ?�메???�비??
RESEND_API_KEY=your_resend_api_key
EMAIL_FROM=your_sender_email

# Celery & Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# 기�?
SECRET_KEY=your_secret_key
DEBUG=false
```

## ?�� 개발 가?�드

### 로컬 개발 ?�정
```bash
# Python 가?�환�??�성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# ?�존???�치
pip install -r requirements.txt

# ?�이?�베?�스 마이그레?�션
alembic upgrade head

# 개발 ?�버 ?�작
uvicorn main:app --reload --port 8000

# Celery Worker ?�작 (별도 ?��???
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo

# Celery Beat ?�작 (별도 ?��???
celery -A app.tasks.celery_app beat --loglevel=info
```

### ??마이그레?�션 ?�성
```bash
alembic revision --autogenerate -m "migration description"
alembic upgrade head
```

## ?�� API 문서

?�버 ?�행 ???�음 URL?�서 API 문서�??�인?????�습?�다:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## ?�� 모니?�링

- Flower (Celery 모니?�링): `http://localhost:5555`
- ?�업 ?�계 API: `/api/v1/monitoring/tasks/statistics`
- ?�스???�태: `/api/v1/monitoring/system/health`

## ?? 배포

### Cloudtype 배포
1. GitHub ?�?�소�?Cloudtype???�결
2. Dockerfile 배포 방식 ?�택
3. ?�경변???�정
4. 배포 ?�행

### ?�경변???�정 (Cloudtype)
Cloudtype ?�?�보?�에???�의 ?�경변?�들??모두 ?�정?�주?�요.

## ?�� ?�이?�스

???�로?�트??MIT ?�이?�스�??�릅?�다.

## ?�� 기여

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## ?�� 문의

- ?�메?? vnfm0580@gmail.com
- GitHub: [woopsmarketing](https://github.com/woopsmarketing) 
