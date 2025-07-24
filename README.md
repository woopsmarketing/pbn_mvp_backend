# PBN Backend API

BacklinkVending PBN ë°±ë§??êµ¬ì¶• ?œë¹„?¤ì˜ ë°±ì—”??API ?œë²„?…ë‹ˆ??

## ?? ì£¼ìš” ê¸°ëŠ¥

- **PBN ë°±ë§???ë™ êµ¬ì¶•**: ë¬´ë£Œ/? ë£Œ PBN ë°±ë§???œë¹„??
- **?¬ìš©???¸ì¦**: Clerk JWT ê¸°ë°˜ ?¸ì¦ ?œìŠ¤??
- **?´ë©”???Œë¦¼**: Resend APIë¥??µí•œ ?ë™ ?´ë©”??ë°œì†¡
- **?‘ì—… ??*: Celery + Redisë¥??µí•œ ë¹„ë™ê¸??‘ì—… ì²˜ë¦¬
- **ëª¨ë‹ˆ?°ë§**: ?‘ì—… ?íƒœ ì¶”ì  ë°?ê´€ë¦??€?œë³´??
- **?°ì´?°ë² ?´ìŠ¤**: Supabase PostgreSQL ?°ë™

## ?›  ê¸°ìˆ  ?¤íƒ

- **Framework**: FastAPI
- **Database**: PostgreSQL (Supabase)
- **Queue**: Celery + Redis
- **Authentication**: Clerk JWT
- **Email**: Resend API
- **Deployment**: Docker + Cloudtype
- **Migration**: Alembic

## ?“‹ API ?”ë“œ?¬ì¸??

### ?¸ì¦
- `POST /api/v1/verify` - JWT ? í° ê²€ì¦?ë°??¬ìš©???±ë¡
- `GET /api/v1/users/me` - ?„ì¬ ?¬ìš©???•ë³´ ì¡°íšŒ

### PBN ?œë¹„??
- `POST /api/v1/pbn/rest-test-request` - ë¬´ë£Œ PBN ë°±ë§???”ì²­ (?ŒìŠ¤?¸ìš©)
- `POST /api/v1/pbn/sample-request` - ë¬´ë£Œ PBN ë°±ë§???”ì²­ (?¸ì¦ ?„ìš”)
- `GET /api/v1/pbn/check-free-usage` - ë¬´ë£Œ PBN ?¬ìš© ?´ë ¥ ?•ì¸
- `GET /api/v1/pbn/rest-orders/{order_id}/status` - ì£¼ë¬¸ ?íƒœ ì¡°íšŒ
- `POST /api/v1/pbn/admin/reset-free-usage/{clerk_id}` - ê´€ë¦¬ì??ë¬´ë£Œ PBN ?œí•œ ?´ì œ

### ëª¨ë‹ˆ?°ë§
- `GET /api/v1/monitoring/tasks/statistics` - ?‘ì—… ?µê³„
- `GET /api/v1/monitoring/system/health` - ?œìŠ¤???íƒœ ?•ì¸
- `GET /api/v1/monitoring/tasks/failed` - ?¤íŒ¨???‘ì—… ì¡°íšŒ

## ?” ë¬´ë£Œ PBN ë°±ë§???œí•œ ?•ì±…

### ?“‹ **1???œí•œ ?•ì±…**
- **??ê³„ì •??1?Œë§Œ** ë¬´ë£Œ PBN ë°±ë§???œë¹„???´ìš© ê°€??
- ?´ë? ?¬ìš©??ê³„ì •?€ ?ë™?¼ë¡œ ì°¨ë‹¨?©ë‹ˆ??
- ì¶”ê? ?´ìš©???í•˜?œë©´ ? ë£Œ ?œë¹„?¤ë? ?´ìš©?´ì£¼?¸ìš”

### ?” **?¬ìš© ?´ë ¥ ?•ì¸**
```bash
# ?„ì¬ ?¬ìš©?ì˜ ë¬´ë£Œ PBN ?¬ìš© ê°€???¬ë? ?•ì¸
GET /api/v1/pbn/check-free-usage
Authorization: Bearer {clerk_jwt_token}
```

### ? ï¸ **?œí•œ ?ìš© ???‘ë‹µ**

**ê°œì„ ???¬ìš©??ì¹œí™”???ëŸ¬ ë©”ì‹œì§€:**
```json
{
  "detail": {
    "success": false,
    "message": "? ï¸ ë¬´ë£Œ PBN ë°±ë§???œë¹„???´ìš© ?œí•œ\n\n?ˆë…•?˜ì„¸??\nì£„ì†¡?˜ì?ë§?ë¬´ë£Œ PBN ë°±ë§???œë¹„?¤ëŠ” ??ê³„ì •??1?Œë§Œ ?´ìš©?˜ì‹¤ ???ˆìŠµ?ˆë‹¤.\n\n?“Š ?„ì¬ ?´ìš© ?„í™©:\n???´ë©”?? user@example.com\n??ì´?ë¬´ë£Œ ì£¼ë¬¸: 1??n??ì§„í–‰ ì¤‘ì¸ ì£¼ë¬¸: 1ê°?n\n?’¡ ??ë§ì? ë°±ë§?¬ê? ?„ìš”?˜ì‹œ?¤ë©´:\n???„ë¦¬ë¯¸ì—„ PBN ë°±ë§???¨í‚¤ì§€ë¥??´ìš©?´ì£¼?¸ìš”\n??ê³ í’ˆì§ˆì˜ ?¤ì–‘??ë°±ë§?¬ë? ?œê³µ?©ë‹ˆ??n??ë¬¸ì˜?¬í•­?€ ?¸ì œ???°ë½ì£¼ì„¸??\n\nê°ì‚¬?©ë‹ˆ???™",
    "title": "ë¬´ë£Œ ?œë¹„???´ìš© ?œí•œ",
    "type": "warning",
    "code": "FREE_PBN_ALREADY_USED",
    "user_info": {
      "email": "user@example.com",
      "total_orders": 1,
      "active_orders": 1
    },
    "recommendations": [
      "?„ë¦¬ë¯¸ì—„ PBN ë°±ë§???¨í‚¤ì§€ ?´ìš©",
      "ê³ í’ˆì§?ë°±ë§???œë¹„??ë¬¸ì˜",
      "ë§ì¶¤??SEO ?ë‹´ ? ì²­"
    ]
  }
}
```

### ?§ª **?ŒìŠ¤??ê³„ì • ?ˆì™¸ ì²˜ë¦¬**

**ë¬´ì œ???¬ìš© ê°€?¥í•œ ?ŒìŠ¤??ê³„ì •:**
- `vnfm0580@gmail.com` (ê´€ë¦¬ì ê³„ì •)
- `mwang12347890@gmail.com` (?ŒìŠ¤??ê³„ì •)

??ê³„ì •?¤ì? ë¬´ë£Œ PBN 1???œí•œ?ì„œ **?ë™?¼ë¡œ ?œì™¸**?˜ì–´ ë¬´ì œ???¬ìš© ê°€?¥í•©?ˆë‹¤.

### ?›  **ê´€ë¦¬ì ?œí•œ ?´ì œ**
```bash
# ê´€ë¦¬ìê°€ ?¹ì • ?¬ìš©?ì˜ ë¬´ë£Œ PBN ?œí•œ ?´ì œ
POST /api/v1/pbn/admin/reset-free-usage/{clerk_id}?reason=ê³ ê°ì§€?ìš”ì²?
Authorization: Bearer {admin_jwt_token}
```

## ?¨ ?„ë¡ ?¸ì—”???ëŸ¬ ì²˜ë¦¬ ê°€?´ë“œ

### **ê°œì„ ???ëŸ¬ ?‘ë‹µ ?œìš©**

?ˆë¡œ???ëŸ¬ ?‘ë‹µ ?•íƒœë¥??œìš©???¬ìš©??ì¹œí™”?ì¸ UIë¥?êµ¬í˜„?????ˆìŠµ?ˆë‹¤:

```javascript
// API ?”ì²­ ???ëŸ¬ ì²˜ë¦¬ ?ˆì œ
try {
  const response = await fetch('/api/v1/pbn/sample-request', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwt_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      target_url: 'https://example.com',
      keyword: 'SEO ë°±ë§??
    })
  });

  if (!response.ok) {
    const errorData = await response.json();
    
    if (errorData.detail?.code === 'FREE_PBN_ALREADY_USED') {
      // ë³´ê¸° ì¢‹ì? ê²½ê³  ?ì—… ?œì‹œ
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
  console.error('API ?”ì²­ ?¤íŒ¨:', error);
}
```

### **ì¶”ì²œ UI ì»´í¬?ŒíŠ¸**

```html
<!-- ê²½ê³  ëª¨ë‹¬ ?ˆì œ -->
<div class="warning-modal">
  <div class="modal-header">
    <h3>? ï¸ ë¬´ë£Œ ?œë¹„???´ìš© ?œí•œ</h3>
  </div>
  <div class="modal-body">
    <div class="user-info">
      <p><strong>?“§ ?´ë©”??</strong> user@example.com</p>
      <p><strong>?“Š ?´ìš© ?„í™©:</strong> 1???¬ìš© ?„ë£Œ</p>
    </div>
    
    <div class="recommendations">
      <h4>?’¡ ì¶”ì²œ ?œë¹„??</h4>
      <ul>
        <li>?„ë¦¬ë¯¸ì—„ PBN ë°±ë§???¨í‚¤ì§€</li>
        <li>ê³ í’ˆì§?ë°±ë§???œë¹„???ë‹´</li>
        <li>ë§ì¶¤??SEO ?„ëµ ?˜ë¦½</li>
      </ul>
    </div>
  </div>
  <div class="modal-footer">
    <button class="btn-primary">?„ë¦¬ë¯¸ì—„ ?œë¹„??ë³´ê¸°</button>
    <button class="btn-secondary">ë¬¸ì˜?˜ê¸°</button>
    <button class="btn-close">?«ê¸°</button>
  </div>
</div>
```

### **?ŒìŠ¤??ê³„ì • ?•ì¸**

?ŒìŠ¤??ê³„ì • ?¬ë????‘ë‹µ??`is_test_account` ?„ë“œë¡??•ì¸?????ˆìŠµ?ˆë‹¤:

```javascript
// ?¬ìš©??ê³„ì • ?íƒœ ?•ì¸
const checkUserStatus = async () => {
  const response = await fetch('/api/v1/pbn/check-free-usage');
  const data = await response.json();
  
  if (data.is_test_account) {
    console.log('?ŒìŠ¤??ê³„ì •: ë¬´ì œ???¬ìš© ê°€??);
    showTestAccountBadge();
  }
};
```

## ?³ Dockerë¡??¤í–‰

### ë¡œì»¬ ê°œë°œ?˜ê²½
```bash
# ?€?¥ì†Œ ?´ë¡ 
git clone https://github.com/woopsmarketing/pbn_mvp_backend.git
cd pbn_mvp_backend

# ?˜ê²½ë³€???¤ì •
cp .env.example .env
# .env ?Œì¼???´ì–´???„ìš”??ê°’ë“¤???¤ì •?˜ì„¸??

# Docker Composeë¡??¤í–‰
docker-compose up -d

# ë§ˆì´ê·¸ë ˆ?´ì…˜ ?¤í–‰
docker-compose exec api alembic upgrade head
```

### ?„ë¡œ?•ì…˜ ë°°í¬ (Cloudtype)
```bash
# Dockerfile???¬ìš©?˜ì—¬ ë°°í¬
# Cloudtype?ì„œ ?˜ê²½ë³€?˜ë? ?¤ì •?˜ê³  ë°°í¬?˜ì„¸??
```

## ?”§ ?˜ê²½ë³€???¤ì •

`.env` ?Œì¼???¤ìŒ ?˜ê²½ë³€?˜ë“¤???¤ì •?´ì•¼ ?©ë‹ˆ??

```env
# ?°ì´?°ë² ?´ìŠ¤
DATABASE_URL=postgresql+psycopg2://user:password@host:port/dbname

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Clerk ?¸ì¦
CLERK_SECRET_KEY=your_clerk_secret
CLERK_JWK_URL=your_jwk_url
CLERK_ISSUER=your_issuer
CLERK_AUDIENCE=your_audience

# ?´ë©”???œë¹„??
RESEND_API_KEY=your_resend_api_key
EMAIL_FROM=your_sender_email

# Celery & Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# ê¸°í?
SECRET_KEY=your_secret_key
DEBUG=false
```

## ?“š ê°œë°œ ê°€?´ë“œ

### ë¡œì»¬ ê°œë°œ ?¤ì •
```bash
# Python ê°€?í™˜ê²??ì„±
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# ?˜ì¡´???¤ì¹˜
pip install -r requirements.txt

# ?°ì´?°ë² ?´ìŠ¤ ë§ˆì´ê·¸ë ˆ?´ì…˜
alembic upgrade head

# ê°œë°œ ?œë²„ ?œì‘
uvicorn main:app --reload --port 8000

# Celery Worker ?œì‘ (ë³„ë„ ?°ë???
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo

# Celery Beat ?œì‘ (ë³„ë„ ?°ë???
celery -A app.tasks.celery_app beat --loglevel=info
```

### ??ë§ˆì´ê·¸ë ˆ?´ì…˜ ?ì„±
```bash
alembic revision --autogenerate -m "migration description"
alembic upgrade head
```

## ?” API ë¬¸ì„œ

?œë²„ ?¤í–‰ ???¤ìŒ URL?ì„œ API ë¬¸ì„œë¥??•ì¸?????ˆìŠµ?ˆë‹¤:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## ?“Š ëª¨ë‹ˆ?°ë§

- Flower (Celery ëª¨ë‹ˆ?°ë§): `http://localhost:5555`
- ?‘ì—… ?µê³„ API: `/api/v1/monitoring/tasks/statistics`
- ?œìŠ¤???íƒœ: `/api/v1/monitoring/system/health`

## ?? ë°°í¬

### Cloudtype ë°°í¬
1. GitHub ?€?¥ì†Œë¥?Cloudtype???°ê²°
2. Dockerfile ë°°í¬ ë°©ì‹ ? íƒ
3. ?˜ê²½ë³€???¤ì •
4. ë°°í¬ ?¤í–‰

### ?˜ê²½ë³€???¤ì • (Cloudtype)
Cloudtype ?€?œë³´?œì—???„ì˜ ?˜ê²½ë³€?˜ë“¤??ëª¨ë‘ ?¤ì •?´ì£¼?¸ìš”.

## ?“ ?¼ì´?¼ìŠ¤

???„ë¡œ?íŠ¸??MIT ?¼ì´?¼ìŠ¤ë¥??°ë¦…?ˆë‹¤.

## ?¤ ê¸°ì—¬

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## ?“ ë¬¸ì˜

- ?´ë©”?? vnfm0580@gmail.com
- GitHub: [woopsmarketing](https://github.com/woopsmarketing) 
